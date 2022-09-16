import asyncio
import concurrent.futures
import bpy
import gc
import typing
from . import globalvar
import sys

# blender cloud add-on
_loop_kicking_operator_running = False


def setup_asyncio_executor():

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
            except Exception as e:
                print("Exception")
                print(e)
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
    _state = 'INITIALIZING'
    stop_upon_exception = False
    timer = None

    # id = -1

    def invoke(self, context, event):
        context.window_manager.modal_handler_add(self)
        self.timer = context.window_manager.event_timer_add(
            1 / 15, window=context.window)
        # print("Starting")
        self._new_async_task(self.async_execute(context))
        # self.id = globalvar.get_id()
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
        # print("MODEL: {0}".format(self.id))
        if task and (task.done() or task.cancelled()):
            print("Task Done {0}".format(task.done()))
            print("Task Cancelled {0}".format(task.cancelled()))
            self._finish(context)
            return {'FINISHED'}

        return {'PASS_THROUGH'}

    def _finish(self, context):
        self._stop_async_task(False)
        context.window_manager.event_timer_remove(self.timer)

    def _new_async_task(self, async_task: typing.Coroutine):
        """Stops the currently running async task, and starts another one."""
        print('Setting up a new task {0}, so any existing task must be stopped'.format(
            async_task))
        self._stop_async_task()

        self.async_task = asyncio.ensure_future(async_task)
        globalvar.async_task = self.async_task
        print('Created new task {0}'.format(globalvar.async_task))

        # Start the async manager so everything happens.
        ensure_async_loop()

    def _stop_async_task(self, is_global=True):
        print('Stopping async task')
        if is_global:
            async_task = globalvar.async_task
        else:
            async_task = self.async_task
        if async_task is None:
            print('No async task, trivially stopped')
            return

        # Signal that we want to stop.
        async_task.cancel()

        # Wait until the asynchronous task is done.
        if not async_task.done():
            print("blocking until async task is done.")
            loop = asyncio.get_event_loop()
            try:
                loop.run_until_complete(async_task)
            except asyncio.CancelledError:
                print('Asynchronous task was cancelled')
                return

        # noinspection PyBroadException
        try:
            # This re-raises any exception of the task.
            async_task.result()
        except asyncio.CancelledError:
            print('Asynchronous task was cancelled')
        except Exception as e:

            print("Exception from asynchronous task")
            print(e)


def register():
    bpy.utils.register_class(Sublender_AsyncLoopModalOperator)


def unregister():
    bpy.utils.unregister_class(Sublender_AsyncLoopModalOperator)
