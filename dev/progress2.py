import time
import sys
from datetime import datetime, timedelta

class TwoLevelProgressBar:
    def __init__(self, bar_width: int = 40):
        self.bar_width = bar_width
        self.level1_total = 0
        self.level1_current = 0
        self.level1_start_time = None
        self.level1_label = ""
        
        self.level2_total = 0
        self.level2_current = 0
        self.level2_start_time = None
        self.level2_label = ""
        
        self.last_display_lines = 0
    
    def start_level1(self, total: int, label: str = "進捗"):
        self.level1_total = total
        self.level1_current = 0
        self.level1_start_time = time.monotonic()
        self.level1_label = label
        self._display()
    
    def start_level2(self, total: int, label: str = "サブ進捗"):
        self.level2_total = total
        self.level2_current = 0
        self.level2_start_time = time.monotonic()
        self.level2_label = label
        self._display()
    
    def update_level1(self, current: int = None):
        if current is not None:
            self.level1_current = current
        else:
            self.level1_current += 1
        self._display()
    
    def update_level2(self, current: int = None):
        if current is not None:
            self.level2_current = current
        else:
            self.level2_current += 1
        self._display()
    
    def finish_level2(self):
        self.level2_total = 0
        self.level2_current = 0
        self.level2_start_time = None
        self.level2_label = ""
        self._display()
    
    def finish(self):
        print()
    
    def _calculate_eta(self, start_time: float, current: int, total: int) -> str:
        """効率的で正確なETA計算"""
        if current == 0 or start_time is None:
            return "計算中..."
        
        elapsed = time.monotonic() - start_time
        if elapsed < 0.001:  # 経過時間がほぼゼロ
            return "計算中..."
        
        # 残り時間計算 (秒単位)
        remaining_time = (elapsed / current) * (total - current)
        
        # 負の時間を防止
        remaining_time = max(0, remaining_time)
        
        # 時間フォーマット変換
        if remaining_time < 60:
            return f"{int(remaining_time)}秒"
        elif remaining_time < 3600:
            return f"{int(remaining_time//60)}分{int(remaining_time%60)}秒"
        else:
            hours = int(remaining_time // 3600)
            minutes = int((remaining_time % 3600) // 60)
            return f"{hours}時間{minutes}分"
    
    def _create_bar(self, current: int, total: int) -> str:
        if total == 0:
            return '-' * self.bar_width
        
        percent = current / total
        filled = int(self.bar_width * percent)
        return '█' * filled + '-' * (self.bar_width - filled)
    
    def _display(self):
        # 前回の表示をクリア
        if self.last_display_lines > 0:
            for _ in range(self.last_display_lines):
                sys.stdout.write('\033[1A')  # カーソルを1行上に
                sys.stdout.write('\033[2K')  # 行をクリア
        
        lines = []
        
        # レベル1表示
        if self.level1_total > 0:
            bar1 = self._create_bar(self.level1_current, self.level1_total)
            percent1 = (self.level1_current / self.level1_total) * 100
            eta1 = self._calculate_eta(self.level1_start_time, self.level1_current, self.level1_total)
            line1 = f"{self.level1_label}: [{bar1}] {self.level1_current}/{self.level1_total} ({percent1:.1f}%) ETA: {eta1}"
            lines.append(line1)
        
        # レベル2表示
        if self.level2_total > 0 and self.level2_start_time is not None:
            bar2 = self._create_bar(self.level2_current, self.level2_total)
            percent2 = (self.level2_current / self.level2_total) * 100
            eta2 = self._calculate_eta(self.level2_start_time, self.level2_current, self.level2_total)
            line2 = f"  {self.level2_label}: [{bar2}] {self.level2_current}/{self.level2_total} ({percent2:.1f}%) ETA: {eta2}"
            lines.append(line2)
        
        # 表示
        for line in lines:
            print(line)
        
        self.last_display_lines = len(lines)
        sys.stdout.flush()


# 使用例
if __name__ == "__main__":
    progress = TwoLevelProgressBar()
    
    # デモンストレーション
    progress.start_level1(5, "メイン処理")
    
    for i in range(5):
        progress.update_level1(i + 1)
        
        # サブタスク
        progress.start_level2(10, f"サブ処理{i+1}")
        for j in range(10):
            progress.update_level2(j + 1)
            time.sleep(0.1)  # シミュレーション
        progress.finish_level2()
    
    progress.finish()
    print("完了!")