from datetime import datetime
import asyncio
import time
from typing import List, Optional, Any, Coroutine, Union


class MyAsync:
    """非同期タスクを管理・実行するクラス（シンプル版）"""

    def __init__(self, stop_on_error: bool = True) -> None:
        """MyAsyncインスタンスを初期化する(stop_on_error: エラー時停止)"""
        self.stop_on_error: bool = stop_on_error
        self.tasks: List[asyncio.Task] = []
        self.loop: Optional[asyncio.AbstractEventLoop] = None
        self.results_cache: Optional[List[Any]] = None
        self.total_time: Optional[float] = None
        self.task_times: Optional[List[float]] = None

    async def _time_wrapper(self, coro: Coroutine) -> tuple[Any, float]:
        """コルーチンの実行時間を測定する"""
        start_time = time.time()
        try:
            result = await coro
            elapsed = time.time() - start_time
            return result, elapsed
        except Exception as e:
            elapsed = time.time() - start_time
            if self.stop_on_error:
                raise e
            return None, elapsed

    def addtask(self, coro: Coroutine[Any, Any, Any]) -> asyncio.Task:
        """コルーチンをタスクとして追加し、実行待ちリストに登録する"""
        if self.loop is None:
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)

        # 時間測定ラッパーでコルーチンを包む
        wrapped_coro = self._time_wrapper(coro)
        task = self.loop.create_task(wrapped_coro)
        self.tasks.append(task)
        self.results_cache = None  # キャッシュをクリア
        self.total_time = None
        self.task_times = None
        return task

    def _execute_all_tasks(self) -> tuple[List[Any], List[float]]:
        """すべてのタスクを実行する"""
        if self.stop_on_error:
            results_and_times = self.loop.run_until_complete(
                asyncio.gather(*self.tasks))
        else:
            results_and_times = self.loop.run_until_complete(
                asyncio.gather(*self.tasks, return_exceptions=True)
            )
            # 例外をNoneに変換
            processed_results = []
            for item in results_and_times:
                if isinstance(item, Exception):
                    processed_results.append((None, 0.0))
                else:
                    processed_results.append(item)
            results_and_times = processed_results

        # 結果と時間を分離
        results, times = zip(
            *results_and_times) if results_and_times else ([], [])
        return list(results), list(times)

    def result(self) -> List[Any]:
        """登録されたすべてのタスクを実行し、結果のリストを返す"""
        if not self.tasks:
            return []

        # キャッシュされた結果があれば返す
        if self.results_cache is not None:
            return self.results_cache

        try:
            start_time = time.time()
            results, task_times = self._execute_all_tasks()
            self.total_time = time.time() - start_time
            self.results_cache = results
            self.task_times = task_times
            return results
        finally:
            pass  # ループは維持(再利用のため)

    def get_total_time(self) -> Optional[float]:
        """総実行時間を返す（result()実行後のみ有効）"""
        return self.total_time

    def get_task_times(self) -> Optional[List[float]]:
        """各タスクの実行時間のリストを返す（result()実行後のみ有効）"""
        return self.task_times

    def clear(self) -> None:
        """すべてのタスクとキャッシュをクリアし、イベントループを閉じる"""
        self.tasks.clear()
        self.results_cache = None
        self.total_time = None
        self.task_times = None
        if self.loop and not self.loop.is_closed():
            self.loop.close()
        self.loop = None


class OpenRouterAsync(MyAsync):
    """OpenRouter用のレート制限対応非同期クラス"""

    def __init__(self, requests_per_interval: int = 50, interval_seconds: int = 10, stop_on_error: bool = True) -> None:
        """OpenRouterAsyncを初期化(requests_per_interval: インターバル内の最大リクエスト数, interval_seconds: インターバル秒数)"""
        super().__init__(stop_on_error)
        self.requests_per_interval = requests_per_interval
        self.interval_seconds = interval_seconds
        self.semaphore: Optional[asyncio.Semaphore] = None
        self.request_times: List[float] = []

    async def _rate_limited_wrapper(self, coro: Coroutine) -> tuple[Any, float]:
        """レート制限付きでコルーチンを実行する"""
        if self.semaphore is None:
            self.semaphore = asyncio.Semaphore(self.requests_per_interval)

        async with self.semaphore:
            current_time = time.time()

            # 古いリクエスト時刻を削除
            cutoff_time = current_time - self.interval_seconds
            self.request_times = [
                t for t in self.request_times if t > cutoff_time]

            # リクエスト数が上限に達している場合は待機
            if len(self.request_times) >= self.requests_per_interval:
                wait_time = self.request_times[0] + \
                    self.interval_seconds - current_time
                if wait_time > 0:
                    await asyncio.sleep(wait_time)
                    current_time = time.time()

            # リクエスト時刻を記録
            self.request_times.append(current_time)

            # 実際のタスク実行
            return await super()._time_wrapper(coro)

    async def _time_wrapper(self, coro: Coroutine) -> tuple[Any, float]:
        """レート制限ラッパーを適用"""
        return await self._rate_limited_wrapper(coro)

async def mySleep(name: str, duration: float) -> str:
    """指定した時間だけ非同期でスリープし、完了メッセージを返す"""
    print(f"mySleep({name}): 開始")
    await asyncio.sleep(duration)
    print(f"mySleep({name}): 終了")
    return f"{name}完了"


async def mySleep(name: str, duration: float) -> str:
    """指定した時間だけ非同期でスリープし、完了メッセージを返す"""
    start_time = datetime.now().strftime("%H:%M:%S.%f")[:-3]
    print(f"[{start_time}] mySleep({name}, {duration:.1f}s): 開始")

    await asyncio.sleep(duration)

    end_time = datetime.now().strftime("%H:%M:%S.%f")[:-3]
    print(f"[{end_time}] mySleep({name}, {duration:.1f}s): 終了")

    return f"{name}完了"


if __name__ == "__main__":
    import random,time

    print("=== OpenRouterAsync（レート制限: 5/1s）===")
    or_runner = OpenRouterAsync(
        requests_per_interval=5, interval_seconds=1, stop_on_error=False)

    time.get

    # 15個のタスクを追加（0.1~5秒のランダム実行時間）
    for i in range(15):
        duration = random.uniform(0.1, 5.0)
        or_runner.addtask(mySleep(f"task{i+1:02d}", duration))

    time.sleep(5)
    print("\npassed 5s \n")
    results = or_runner.result()
    print("結果:", results)
    print(f"総実行時間: {or_runner.get_total_time():.2f}秒")
    print(f"個別タスク時間: {[f'{t:.2f}' for t in or_runner.get_task_times()]}")
    or_runner.clear()
