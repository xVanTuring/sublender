import asyncio
import concurrent.futures
import bpy
import gc
import typing
# blender cloud addon
_loop_kicking_operator_running = False


def setup_asyncio_executor():
    import sys

    if sys.platform == 'win32':
        asyncio.get_event_loop().close()
        # On Windows, the default event loop is SelectorEventLoop, which does
        # not support subprocesses. ProactorEventLoop should be used instead.
        # Source: https://docs.python.org/3/library/asyncio-subprocess.html
        loop = asyncio.ProactorEventLoop()
        asyncio.set_event_loop(loop)
    else:
        loop = asyncio.get_event_loop()

    executor = concurrent.futures.ThreadPoolExecutor(max_workers=3)
    loop.set_default_executor(executor)


def kick_async_loop(*args) -> bool:
    loop = asyncio.get_event_loop()
    stop_after_this_kick = False
    if loop.is_closed():
        print('loop closed, stopping immediately.')
        return True
    all_tasks = asyncio.Task.all_tasks()
    if not len(all_tasks):
        stop_after_this_kick = True
    elif all(task.done() for task in all_tasks):
        stop_after_this_kick = True
        gc.collect()
        for task_idx, task in enumerate(all_tasks):
            if not task.done():
                continue
            try:
                res = task.result()
            except asyncio.CancelledError:
                print("asyncio.CancelledError")
            except Exception:
                print("Exception")
    loop.stop()
    loop.run_forever()
    return stop_after_this_kick


def ensure_async_loop():
    result = bpy.ops.sublender.asyncio_loop()
    print("asyncio_loop")
    print(result)


class Sublender_AsyncLoopModalOperator(bpy.types.Operator):
    bl_idname = "sublender.asyncio_loop"
    bl_label = "..."

    def execute(self, context):
        return self.invoke(context, None)

    def invoke(self, context, event):
        global _loop_kicking_operator_running
        if _loop_kicking_operator_running:
            return {'PASS_THROUGH'}

        context.window_manager.modal_handler_add(self)
        _loop_kicking_operator_running = True
        wm = context.window_manager
        self.timer = wm.event_timer_add(0.03, window=context.window)
        return {'RUNNING_MODAL'}

    def modal(self, context, event):
        # print("I'm modal from Sublender_AsyncLoopModalOperator")
        global _loop_kicking_operator_running
        if not _loop_kicking_operator_running:
            return {'FINISHED'}

        if event.type != 'TIMER':
            return {'PASS_THROUGH'}

        stop_after = kick_async_loop()
        if stop_after:
            context.window_manager.event_timer_remove(self.timer)
            _loop_kicking_operator_running = False
            return {'FINISHED'}

        return {'RUNNING_MODAL'}


class AsyncModalOperatorMixin:
    async_task = None  # asyncio task for fetching thumbnails
    # asyncio future for signalling that we want to cancel everything.
    signalling_future = None
    _state = 'INITIALIZING'
    stop_upon_exception = False

    def invoke(self, context, event):
        context.window_manager.modal_handler_add(self)
        self.timer = context.window_manager.event_timer_add(
            1/15, window=context.window)
        print("Starting")
        self._new_async_task(self.async_execute(context))
        return {'RUNNING_MODAL'}

    async def async_execute(self, context):
        """Entry point of the asynchronous operator.

        Implement in a subclass.
        """
        return

    def quit(self):
        """Signals the state machine to stop this operator from running."""
        self._state = 'QUIT'

    def execute(self, context):
        return self.invoke(context, None)

    def modal(self, context, event):
        task = self.async_task

        if self._state != 'EXCEPTION' and task and task.done() and not task.cancelled():
            ex = task.exception()
            if ex is not None:
                self._state = 'EXCEPTION'
                print('Exception while running task: {0}'.format(ex))
                if self.stop_upon_exception:
                    self.quit()
                    self._finish(context)
                    return {'FINISHED'}

                return {'RUNNING_MODAL'}

        if self._state == 'QUIT':
            self._finish(context)
            return {'FINISHED'}

        return {'PASS_THROUGH'}

    def _finish(self, context):
        self._stop_async_task()
        context.window_manager.event_timer_remove(self.timer)

    def _new_async_task(self, async_task: typing.Coroutine, future: asyncio.Future = None):
        """Stops the currently running async task, and starts another one."""
        print('Setting up a new task {0}, so any existing task must be stopped'.format(
            async_task))
        self._stop_async_task()

        # Download the previews asynchronously.
        self.signalling_future = future or asyncio.Future()
        self.async_task = asyncio.ensure_future(async_task)
        print('Created new task {0}'.format(self.async_task))

        # Start the async manager so everything happens.
        ensure_async_loop()

    def _stop_async_task(self):
        print('Stopping async task')
        if self.async_task is None:
            print('No async task, trivially stopped')
            return

        # Signal that we want to stop.
        self.async_task.cancel()
        if not self.signalling_future.done():
            print(
                "Signalling that we want to cancel anything that's running.")
            self.signalling_future.cancel()

        # Wait until the asynchronous task is done.
        if not self.async_task.done():
            print("blocking until async task is done.")
            loop = asyncio.get_event_loop()
            try:
                loop.run_until_complete(self.async_task)
            except asyncio.CancelledError:
                print('Asynchronous task was cancelled')
                return

        # noinspection PyBroadException
        try:
            # This re-raises any exception of the task.
            self.async_task.result()
        except asyncio.CancelledError:
            print('Asynchronous task was cancelled')
        except Exception:
            print("Exception from asynchronous task")


def register():
    bpy.utils.register_class(Sublender_AsyncLoopModalOperator)


def unregister():
    bpy.utils.unregister_class(Sublender_AsyncLoopModalOperator)
