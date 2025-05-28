"""
共通基底ウィンドウクラス
全てのウィンドウが継承する基底クラス
"""

import customtkinter as ctk
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from utils import log


class BaseWindow(ctk.CTkToplevel, ABC):
    """全ウィンドウの基底クラス"""
    
    def __init__(self, parent: Optional[ctk.CTk | ctk.CTkToplevel] = None, 
                 title: str = "LLMflashCard", 
                 width: int = 800, 
                 height: int = 600,
                 resizable: bool = True):
        """
        基底ウィンドウの初期化
        
        Args:
            parent: 親ウィンドウ
            title: ウィンドウタイトル
            width: 幅
            height: 高さ
            resizable: リサイズ可能かどうか
        """
        super().__init__(parent)
        
        # ウィンドウ設定
        self.title(title)
        self.geometry(f"{width}x{height}")
        
        if not resizable:
            self.resizable(False, False)
        
        # センタリング
        self.center_window(width, height)
        
        # ウィンドウが閉じられる時のイベント
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # 初期化完了フラグ
        self._initialized = False
        
        log.info(f"BaseWindow initialized: {title} ({width}x{height})")
    
    def center_window(self, width: int, height: int):
        """ウィンドウを画面中央に配置"""
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        
        self.geometry(f"{width}x{height}+{x}+{y}")
    
    @abstractmethod
    def setup_ui(self):
        """UIセットアップ（サブクラスで必須実装）"""
        pass
    
    @abstractmethod
    def setup_bindings(self):
        """イベントバインディングセットアップ（サブクラスで必須実装）"""
        pass
    
    def initialize(self):
        """ウィンドウの初期化処理"""
        if self._initialized:
            log.warning("Window already initialized")
            return
        
        try:
            self.setup_ui()
            self.setup_bindings()
            self._initialized = True
            log.info(f"Window initialization completed: {self.title()}")
        except Exception as e:
            log.error(f"Failed to initialize window: {e}")
            raise
    
    def on_closing(self):
        """ウィンドウ閉じる時の処理"""
        try:
            self.cleanup()
            self.destroy()
            log.info(f"Window closed: {self.title()}")
        except Exception as e:
            log.error(f"Error during window closing: {e}")
            self.destroy()
    
    def cleanup(self):
        """リソースクリーンアップ（サブクラスでオーバーライド可能）"""
        pass
    
    def show_error(self, message: str, title: str = "エラー"):
        """エラーダイアログ表示"""
        from tkinter import messagebox
        messagebox.showerror(title, message, parent=self)
        log.error(f"Error dialog shown: {message}")
    
    def show_info(self, message: str, title: str = "情報"):
        """情報ダイアログ表示"""
        from tkinter import messagebox
        messagebox.showinfo(title, message, parent=self)
        log.info(f"Info dialog shown: {message}")
    
    def show_warning(self, message: str, title: str = "警告"):
        """警告ダイアログ表示"""
        from tkinter import messagebox
        messagebox.showwarning(title, message, parent=self)
        log.warning(f"Warning dialog shown: {message}")
    
    def ask_yes_no(self, message: str, title: str = "確認") -> bool:
        """Yes/No確認ダイアログ"""
        from tkinter import messagebox
        result = messagebox.askyesno(title, message, parent=self)
        log.info(f"Confirmation dialog: {message} -> {result}")
        return result


class BaseMainWindow(ctk.CTk, ABC):
    """メインウィンドウの基底クラス"""
    
    def __init__(self, title: str = "LLMflashCard", width: int = 1200, height: int = 800):
        """
        メインウィンドウの初期化
        
        Args:
            title: ウィンドウタイトル
            width: 幅
            height: 高さ
        """
        super().__init__()
        
        # ウィンドウ設定
        self.title(title)
        self.geometry(f"{width}x{height}")
        
        # センタリング
        self.center_window(width, height)
        
        # ウィンドウが閉じられる時のイベント
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # 初期化完了フラグ
        self._initialized = False
        
        log.info(f"BaseMainWindow initialized: {title} ({width}x{height})")
    
    def center_window(self, width: int, height: int):
        """ウィンドウを画面中央に配置"""
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        
        self.geometry(f"{width}x{height}+{x}+{y}")
    
    @abstractmethod
    def setup_ui(self):
        """UIセットアップ（サブクラスで必須実装）"""
        pass
    
    @abstractmethod
    def setup_bindings(self):
        """イベントバインディングセットアップ（サブクラスで必須実装）"""
        pass
    
    def initialize(self):
        """ウィンドウの初期化処理"""
        if self._initialized:
            log.warning("MainWindow already initialized")
            return
        
        try:
            self.setup_ui()
            self.setup_bindings()
            self._initialized = True
            log.info(f"MainWindow initialization completed: {self.title()}")
        except Exception as e:
            log.error(f"Failed to initialize main window: {e}")
            raise
    
    def on_closing(self):
        """アプリケーション終了時の処理"""
        try:
            self.cleanup()
            log.info("Application closing")
            self.quit()
            self.destroy()
        except Exception as e:
            log.error(f"Error during application closing: {e}")
            self.quit()
    
    def cleanup(self):
        """リソースクリーンアップ（サブクラスでオーバーライド可能）"""
        pass
    
    def show_error(self, message: str, title: str = "エラー"):
        """エラーダイアログ表示"""
        from tkinter import messagebox
        messagebox.showerror(title, message, parent=self)
        log.error(f"Error dialog shown: {message}")
    
    def show_info(self, message: str, title: str = "情報"):
        """情報ダイアログ表示"""
        from tkinter import messagebox
        messagebox.showinfo(title, message, parent=self)
        log.info(f"Info dialog shown: {message}")
    
    def show_warning(self, message: str, title: str = "警告"):
        """警告ダイアログ表示"""
        from tkinter import messagebox
        messagebox.showwarning(title, message, parent=self)
        log.warning(f"Warning dialog shown: {message}")
    
    def ask_yes_no(self, message: str, title: str = "確認") -> bool:
        """Yes/No確認ダイアログ"""
        from tkinter import messagebox
        result = messagebox.askyesno(title, message, parent=self)
        log.info(f"Confirmation dialog: {message} -> {result}")
        return result