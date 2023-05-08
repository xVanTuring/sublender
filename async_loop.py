import asyncio
import concurrent.futures
import gc
import logging
import sys
import traceback
import typing

import bpy

from . import globalvar

_loop_kicking_operator_running = False
log = logging.getLogger(__name__)


def setup_asyncio_executor():
    if sys.platform == 'win32':
        asyncio.get_event_loop().close()
        # On Windows, the default event loop is SelectorEventLoop, which does
        # not support subprocesses. ProactorEventLoop should be used instead.
        # Source: https://docs.python.org/3/library/asyncio-subprocess.html
        loop = asyncio.ProactorEventLoop()
        asyncio.set_event_loop(loop)
        # asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    else:
        loop = asyncio.get_event_loop()

    executor = concurrent.futures.ThreadPoolExecutor(max_workers=3)
    loop.set_default_executor(executor)


def kick_async_loop() -> bool:
    loop = asyncio.get_event_loop()
    stop_after_this_kick = False
    if loop.is_closed():
        return True
    all_tasks = asyncio.all_tasks(loop=loop)
    if not len(all_tasks):
        stop_after_this_kick = True
    elif all(task.done() for task in all_tasks):
        stop_after_this_kick = True
        gc.collect()
        for task_idx, task in enumerate(all_tasks):
            if not task.done():
                continue
            # noinspection PyBroadException
            try:
                res = task.result()
                log.debug('   task #%i: result=%r', task_idx, res)
            except asyncio.CancelledError:
                pass
            except Exception:
                log.warning('{}: resulted in exception'.format(task))
                traceback.print_exc()
    loop.stop()
    loop.run_forever()
    return stop_after_this_kick


def ensure_async_loop():
    log.debug('Starting asyncio loop')
    result = bpy.ops.sublender.asyncio_loop()
    log.debug('Result of starting modal operator is %r', result)


class Sublender_AsyncLoopModalOperator(bpy.types.Operator):
    bl_idname = "sublender.asyncio_loop"
    bl_label = "Runs the asyncio main loop"
    timer = None
    log = logging.getLogger(__name__ + '.SublenderAsyncLoopModalOperator')

    def execute(self, context):
        return self.invoke(context, None)

    def invoke(self, context, _):
        global _loop_kicking_operator_running
        if _loop_kicking_operator_running:
            self.log.debug('Another loop-kicking operator is already running.')
            return {'PASS_THROUGH'}

        context.window_manager.modal_handler_add(self)
        _loop_kicking_operator_running = True

        wm = context.window_manager
        self.timer = wm.event_timer_add(0.03, window=context.window)
        return {'RUNNING_MODAL'}

    def modal(self, context, event):
        global _loop_kicking_operator_running

        if not _loop_kicking_operator_running:
            return {'FINISHED'}

        if event.type != 'TIMER':
            return {'PASS_THROUGH'}

        stop_after = kick_async_loop()
        if stop_after:
            context.window_manager.event_timer_remove(self.timer)
            _loop_kicking_operator_running = False
            self.log.debug('Stopped asyncio loop kicking')
            return {'FINISHED'}

        return {'RUNNING_MODAL'}


class AsyncModalOperatorMixin:
    task_id = None
    async_task = None  # asyncio task for fetching thumbnails
    # asyncio future for signalling that we want to cancel everything.
    stop_upon_exception = False
    timer = None
    log = logging.getLogger('%s.AsyncModalOperatorMixin' % __name__)
    single_task = False

    def invoke(self, context, event):
        context.window_manager.modal_handler_add(self)
        self.timer = context.window_manager.event_timer_add(1 / 15, window=context.window)
        self._new_async_task(self.async_execute(context))
        return {'RUNNING_MODAL'}

    async def async_execute(self, context):
        """Entry point of the asynchronous operator.

        Implement in a subclass.
        """
        return

    def clean(self, context):
        return

    def execute(self, context):
        return self.invoke(context, None)

    def modal(self, context, _):
        task = self.async_task
        if task and (task.done() or task.cancelled()):
            self.log.info('Task was cancelled/done {}/{}'.format(task.cancelled(), task.done()))
            context.window_manager.event_timer_remove(self.timer)
            # noinspection PyBroadException
            try:
                self.async_task.result()
            except asyncio.CancelledError:
                self.log.info('modal: Asynchronous task was cancelled')
            except Exception:
                self.log.exception("modal: Exception from asynchronous task")
            self.clean(context)
            return {'FINISHED'}

        return {'PASS_THROUGH'}

    def _new_async_task(self, async_task: typing.Coroutine):
        if self.single_task:
            self._stop_prev_async_task()

        self.async_task = asyncio.ensure_future(async_task)
        self.log.info("Running task id {}".format(self.task_id))
        if self.single_task:
            globalvar.async_task_map[self.task_id] = self.async_task

        ensure_async_loop()

    def _stop_prev_async_task(self):
        async_task = globalvar.async_task_map.get(self.task_id)
        if async_task is None:
            return
        cancelled = async_task.cancel()
        if not cancelled:
            self.log.info("Previous Task had Completed with id {}".format(self.task_id))
        else:
            self.log.info("Canceling task with id {}".format(self.task_id))

        # Wait until the asynchronous task is done.
        if not async_task.done():
            loop = asyncio.get_event_loop()
            try:
                self.log.info("Wait task to complete, id {}".format(self.task_id))
                loop.run_until_complete(async_task)
            except asyncio.CancelledError:
                self.log.info('Asynchronous task was cancelled')
                return

        # noinspection PyBroadException
        try:
            # This re-raises any exception of the task.
            async_task.result()
        except asyncio.CancelledError:
            self.log.info('Asynchronous task was cancelled')
        except Exception:
            self.log.exception("Exception from asynchronous task")


def register():
    bpy.utils.register_class(Sublender_AsyncLoopModalOperator)


def unregister():
    bpy.utils.unregister_class(Sublender_AsyncLoopModalOperator)
