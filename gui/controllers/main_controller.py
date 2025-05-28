"""
メインコントローラー

アプリケーション全体の制御を担当します。
"""

from typing import Dict, Any, Optional, Callable
from abc import ABC, abstractmethod

from utils import log


class BaseController(ABC):
    """コントローラーの基底クラス"""
    
    def __init__(self):
        self._view: Optional[Any] = None
        self._callbacks: Dict[str, list[Callable]] = {}
        
    def set_view(self, view: Any) -> None:
        """ビューを設定"""
        self._view = view
        log.info(f"{self.__class__.__name__}: ビューを設定しました")
        
    def register_callback(self, event: str, callback: Callable) -> None:
        """コールバック関数を登録"""
        if event not in self._callbacks:
            self._callbacks[event] = []
        self._callbacks[event].append(callback)
        log.info(f"{self.__class__.__name__}: イベント '{event}' にコールバックを登録")
        
    def trigger_callback(self, event: str, *args, **kwargs) -> None:
        """コールバック関数を実行"""
        if event in self._callbacks:
            for callback in self._callbacks[event]:
                try:
                    callback(*args, **kwargs)
                except Exception as e:
                    log.error(f"コールバック実行エラー (event: {event}): {e}")
    
    @abstractmethod
    def initialize(self) -> None:
        """コントローラーの初期化処理"""
        pass
        
    @abstractmethod
    def cleanup(self) -> None:
        """リソースクリーンアップ"""
        pass


class MainController(BaseController):
    """メインアプリケーションコントローラー"""
    
    def __init__(self):
        super().__init__()
        self._child_controllers: Dict[str, BaseController] = {}
        self._application_state: Dict[str, Any] = {
            'current_mode': 'main',  # main, flashcard, image
            'window_size': (1200, 800),
            'theme': 'default',
            'debug_mode': False
        }
        
    def initialize(self) -> None:
        """メインコントローラーの初期化"""
        log.info("MainController: 初期化を開始します")
        
        # アプリケーション状態の初期化
        self._initialize_application_state()
        
        log.info("MainController: 初期化が完了しました")
        
    def cleanup(self) -> None:
        """リソースクリーンアップ"""
        log.info("MainController: クリーンアップを開始します")
        
        # 子コントローラーのクリーンアップ
        for name, controller in self._child_controllers.items():
            try:
                controller.cleanup()
                log.info(f"MainController: {name}コントローラーをクリーンアップしました")
            except Exception as e:
                log.error(f"MainController: {name}コントローラークリーンアップエラー: {e}")
                
        self._child_controllers.clear()
        log.info("MainController: クリーンアップが完了しました")
        
    def register_child_controller(self, name: str, controller: BaseController) -> None:
        """子コントローラーを登録"""
        self._child_controllers[name] = controller
        log.info(f"MainController: {name}コントローラーを登録しました")
        
    def get_child_controller(self, name: str) -> Optional[BaseController]:
        """子コントローラーを取得"""
        return self._child_controllers.get(name)
        
    def set_application_state(self, key: str, value: Any) -> None:
        """アプリケーション状態を設定"""
        old_value = self._application_state.get(key)
        self._application_state[key] = value
        
        if old_value != value:
            log.info(f"MainController: アプリケーション状態更新 {key}: {old_value} -> {value}")
            self.trigger_callback('state_changed', key, value, old_value)
            
    def get_application_state(self, key: str, default: Any = None) -> Any:
        """アプリケーション状態を取得"""
        return self._application_state.get(key, default)
        
    def switch_mode(self, mode: str) -> None:
        """アプリケーションモードを切り替え"""
        if mode not in ['main', 'flashcard', 'image']:
            log.warning(f"MainController: 無効なモード '{mode}' が指定されました")
            return
            
        old_mode = self._application_state.get('current_mode')
        if old_mode != mode:
            self.set_application_state('current_mode', mode)
            log.info(f"MainController: モードを切り替えました {old_mode} -> {mode}")
            self.trigger_callback('mode_changed', mode, old_mode)
            
    def handle_menu_action(self, action: str, *args, **kwargs) -> None:
        """メニューアクションを処理"""
        log.info(f"MainController: メニューアクション '{action}' を処理します")
        
        try:
            if action == 'new_flashcard':
                self._handle_new_flashcard()
            elif action == 'import_flashcard':
                self._handle_import_flashcard()
            elif action == 'export_flashcard':
                self._handle_export_flashcard()
            elif action == 'manage_images':
                self._handle_manage_images()
            elif action == 'settings':
                self._handle_settings()
            elif action == 'about':
                self._handle_about()
            elif action == 'exit':
                self._handle_exit()
            else:
                log.warning(f"MainController: 未知のメニューアクション '{action}'")
                
        except Exception as e:
            log.error(f"MainController: メニューアクション処理エラー '{action}': {e}")
            self.trigger_callback('error', f"メニュー操作でエラーが発生しました: {e}")
            
    def handle_window_event(self, event: str, *args, **kwargs) -> None:
        """ウィンドウイベントを処理"""
        log.info(f"MainController: ウィンドウイベント '{event}' を処理します")
        
        try:
            if event == 'resize':
                width, height = args[0], args[1]
                self._handle_window_resize(width, height)
            elif event == 'close':
                self._handle_window_close()
            elif event == 'minimize':
                self._handle_window_minimize()
            elif event == 'maximize':
                self._handle_window_maximize()
            else:
                log.info(f"MainController: ウィンドウイベント '{event}' は処理されませんでした")
                
        except Exception as e:
            log.error(f"MainController: ウィンドウイベント処理エラー '{event}': {e}")
            
    def _initialize_application_state(self) -> None:
        """アプリケーション状態の初期化"""
        log.info("MainController: アプリケーション状態を初期化します")
        
        # デフォルト設定の適用
        self._application_state.update({
            'current_mode': 'main',
            'window_size': (1200, 800),
            'theme': 'default',
            'debug_mode': False,
            'last_opened_directory': None,
            'recent_files': []
        })
        
    def _handle_new_flashcard(self) -> None:
        """新規フラッシュカード作成"""
        log.info("MainController: 新規フラッシュカード作成を開始")
        self.switch_mode('flashcard')
        self.trigger_callback('new_flashcard_requested')
        
    def _handle_import_flashcard(self) -> None:
        """フラッシュカードインポート"""
        log.info("MainController: フラッシュカードインポートを開始")
        self.trigger_callback('import_flashcard_requested')
        
    def _handle_export_flashcard(self) -> None:
        """フラッシュカードエクスポート"""
        log.info("MainController: フラッシュカードエクスポートを開始")
        self.trigger_callback('export_flashcard_requested')
        
    def _handle_manage_images(self) -> None:
        """画像管理"""
        log.info("MainController: 画像管理を開始")
        self.switch_mode('image')
        self.trigger_callback('image_management_requested')
        
    def _handle_settings(self) -> None:
        """設定画面表示"""
        log.info("MainController: 設定画面を表示")
        self.trigger_callback('settings_requested')
        
    def _handle_about(self) -> None:
        """アバウト画面表示"""
        log.info("MainController: アバウト画面を表示")
        self.trigger_callback('about_requested')
        
    def _handle_exit(self) -> None:
        """アプリケーション終了"""
        log.info("MainController: アプリケーション終了を開始")
        self.trigger_callback('exit_requested')
        
    def _handle_window_resize(self, width: int, height: int) -> None:
        """ウィンドウリサイズ処理"""
        self.set_application_state('window_size', (width, height))
        
    def _handle_window_close(self) -> None:
        """ウィンドウクローズ処理"""
        log.info("MainController: ウィンドウクローズイベントを処理")
        self.trigger_callback('window_close_requested')
        
    def _handle_window_minimize(self) -> None:
        """ウィンドウ最小化処理"""
        log.info("MainController: ウィンドウが最小化されました")
        
    def _handle_window_maximize(self) -> None:
        """ウィンドウ最大化処理"""
        log.info("MainController: ウィンドウが最大化されました")