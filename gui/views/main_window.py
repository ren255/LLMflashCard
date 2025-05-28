"""
メインウィンドウ

アプリケーションのメインウィンドウを定義します。
"""

import tkinter as tk
import customtkinter as ctk
from typing import Optional, Callable, Any
from utils import log

from gui.components import (
    BaseMainWindow,
    StatusBar,
)

ctk.set_appearance_mode("System")  # "System", "Dark", "Light"
ctk.set_default_color_theme("blue")  # "blue", "green", "dark-blue"


class MainWindow(BaseMainWindow):
    """メインアプリケーションウィンドウ"""
    
    def __init__(self):
        """メインウィンドウの初期化"""
        super().__init__()
        self.title("LLM FlashCard")
        self.geometry("1200x800")
        self.minsize(800, 600)
        
        self.current_mode = "main"
        self.controller: Optional[Any] = None

        # UI要素
        self.menu_bar: Optional[tk.Menu] = None
        self.toolbar: Optional[ctk.CTkFrame] = None
        self.main_frame: Optional[ctk.CTkFrame] = None
        self.status_bar: Optional[StatusBar] = None
        
        # モード切り替え用のフレーム
        self.mode_frames: dict[str, ctk.CTkFrame] = {}
        
        self.initialize()
        log.info("メインウィンドウが初期化されました")
    
    def setup_ui(self) -> None:
        """UIセットアップ"""
        log.info("メインウィンドウのUI構築開始")
        
        self._create_menu_bar()
        self._create_toolbar()
        self._create_main_frame()
        self._create_status_bar()
        self._create_main_mode()
        
        self.switch_mode("main")
        
        log.info("メインウィンドウのUI構築完了")
    
    def _create_menu_bar(self) -> None:
        """メニューバーを作成"""
        self.menu_bar = tk.Menu(self)
        self.config(menu=self.menu_bar)
        
        # ファイルメニュー
        file_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="ファイル", menu=file_menu)
        file_menu.add_command(label="新規作成", command=lambda: self._handle_menu_action("new"))
        file_menu.add_command(label="開く", command=lambda: self._handle_menu_action("open"))
        file_menu.add_separator()
        file_menu.add_command(label="終了", command=self.on_closing)
        
        # 表示メニュー
        view_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="表示", menu=view_menu)
        view_menu.add_command(label="フラッシュカード管理", command=lambda: self.switch_mode("flashcard"))
        view_menu.add_command(label="画像管理", command=lambda: self.switch_mode("image"))
        view_menu.add_command(label="メイン画面", command=lambda: self.switch_mode("main"))
        
        # ツールメニュー
        tools_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="ツール", menu=tools_menu)
        tools_menu.add_command(label="設定", command=lambda: self._handle_menu_action("settings"))
        
        # ヘルプメニュー
        help_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="ヘルプ", menu=help_menu)
        help_menu.add_command(label="バージョン情報", command=lambda: self._handle_menu_action("about"))
    
    def _create_toolbar(self) -> None:
        """ツールバーを作成"""
        self.toolbar = ctk.CTkFrame(self, height=50)
        self.toolbar.pack(fill="x", padx=5, pady=(5, 0))
        self.toolbar.pack_propagate(False)
        
        # モード切り替えボタン
        mode_frame = ctk.CTkFrame(self.toolbar)
        mode_frame.pack(side="left", fill="y", padx=(10, 5))
        
        ctk.CTkButton(
            mode_frame,
            text="メイン",
            command=lambda: self.switch_mode("main"),
            width=80,
            height=30
        ).pack(side="left", padx=2, pady=10)
        
        ctk.CTkButton(
            mode_frame,
            text="フラッシュカード",
            command=lambda: self.switch_mode("flashcard"),
            width=100,
            height=30
        ).pack(side="left", padx=2, pady=10)
        
        ctk.CTkButton(
            mode_frame,
            text="画像管理",
            command=lambda: self.switch_mode("image"),
            width=80,
            height=30
        ).pack(side="left", padx=2, pady=10)
        
        # 区切り線
        separator = ctk.CTkFrame(self.toolbar, width=2, fg_color="gray")
        separator.pack(side="left", fill="y", padx=10, pady=5)
        
        # 右側のツールボタン
        tools_frame = ctk.CTkFrame(self.toolbar)
        tools_frame.pack(side="right", fill="y", padx=(5, 10))
        
        ctk.CTkButton(
            tools_frame,
            text="設定",
            command=lambda: self._handle_menu_action("settings"),
            width=60,
            height=30
        ).pack(side="right", padx=2, pady=10)
    
    def _create_main_frame(self) -> None:
        """メインフレームを作成"""
        self.main_frame = ctk.CTkFrame(self)
        self.main_frame.pack(fill="both", expand=True, padx=5, pady=5)
    
    def _create_status_bar(self) -> None:
        """ステータスバーを作成"""
        self.status_bar = StatusBar(self)
        self.status_bar.pack(fill="x", side="bottom")
        self.status_bar.set_status("準備完了")
    
    def _create_main_mode(self) -> None:
        """メインモードのフレームを作成"""
        main_mode_frame = ctk.CTkFrame(self.main_frame)
        
        # ウェルカムメッセージ
        welcome_label = ctk.CTkLabel(
            main_mode_frame,
            text="LLM FlashCard へようこそ",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        welcome_label.pack(pady=(50, 20))
        
        # 説明文
        description_label = ctk.CTkLabel(
            main_mode_frame,
            text="AIを活用したフラッシュカード学習システムです。\n上部のボタンから機能を選択してください。",
            font=ctk.CTkFont(size=14)
        )
        description_label.pack(pady=10)
        
        # クイックアクションボタン
        button_frame = ctk.CTkFrame(main_mode_frame)
        button_frame.pack(pady=30)
        
        ctk.CTkButton(
            button_frame,
            text="フラッシュカード管理",
            command=lambda: self.switch_mode("flashcard"),
            width=200,
            height=40,
            font=ctk.CTkFont(size=14)
        ).pack(pady=5)
        
        ctk.CTkButton(
            button_frame,
            text="画像管理",
            command=lambda: self.switch_mode("image"),
            width=200,
            height=40,
            font=ctk.CTkFont(size=14)
        ).pack(pady=5)
        
        self.mode_frames["main"] = main_mode_frame
    
    def switch_mode(self, mode: str) -> None:
        """モードを切り替え"""
        if mode == self.current_mode:
            return
        
        log.info(f"モードを切り替え: {self.current_mode} -> {mode}")
        
        # 現在のフレームを非表示
        if self.current_mode in self.mode_frames:
            self.mode_frames[self.current_mode].pack_forget()
        
        # 新しいフレームを表示
        if mode in self.mode_frames:
            self.mode_frames[mode].pack(fill="both", expand=True, padx=10, pady=10)
        else:
            # まだ作成されていないモードの場合、プレースホルダーを表示
            self._create_placeholder_mode(mode)
        
        self.current_mode = mode
        
        # ステータスバー更新
        mode_names = {
            "main": "メイン画面",
            "flashcard": "フラッシュカード管理",
            "image": "画像管理"
        }
        self.status_bar.set_status(f"現在のモード: {mode_names.get(mode, mode)}")
        
        # コントローラーに通知
        if self.controller:
            try:
                self.controller.switch_mode(mode)
            except AttributeError:
                log.warning("コントローラーにswitch_modeメソッドがありません")
    
    def _create_placeholder_mode(self, mode: str) -> None:
        """プレースホルダーモードを作成"""
        placeholder_frame = ctk.CTkFrame(self.main_frame)
        
        placeholder_label = ctk.CTkLabel(
            placeholder_frame,
            text=f"{mode} モード",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        placeholder_label.pack(expand=True)
        
        description_label = ctk.CTkLabel(
            placeholder_frame,
            text="この機能は開発中です。",
            font=ctk.CTkFont(size=14)
        )
        description_label.pack()
        
        self.mode_frames[mode] = placeholder_frame
        placeholder_frame.pack(fill="both", expand=True, padx=10, pady=10)
    
    def _handle_menu_action(self, action: str) -> None:
        """メニューアクションを処理"""
        log.info(f"メニューアクション実行: {action}")
        
        if self.controller:
            try:
                self.controller.handle_menu_action(action)
            except AttributeError:
                log.warning("コントローラーにhandle_menu_actionメソッドがありません")
        else:
            # 基本的なアクションのフォールバック処理
            if action == "about":
                self.show_info("LLM FlashCard", "バージョン 1.0.0\nAI活用フラッシュカード学習システム")
            elif action == "settings":
                self.show_info("設定", "設定機能は開発中です。")
            else:
                self.show_info("情報", f"アクション '{action}' は開発中です。")
    
    def set_controller(self, controller: Any) -> None:
        """コントローラーを設定"""
        self.controller = controller
        log.info("メインウィンドウにコントローラーが設定されました")
    
    def setup_bindings(self) -> None:
        """キーボードショートカットを設定"""
        # Ctrl+Q で終了
        self.bind("<Control-q>", lambda e: self.on_closing())
        
        # F1 でヘルプ
        self.bind("<F1>", lambda e: self._handle_menu_action("about"))
        
        # Ctrl+1, 2, 3 でモード切り替え
        self.bind("<Control-1>", lambda e: self.switch_mode("main"))
        self.bind("<Control-2>", lambda e: self.switch_mode("flashcard"))
        self.bind("<Control-3>", lambda e: self.switch_mode("image"))
        
        log.info("キーボードショートカットが設定されました")
    
    def on_closing(self) -> None:
        """ウィンドウクローズ処理"""
        if self.ask_yes_no("確認", "アプリケーションを終了しますか？"):
            log.info("メインウィンドウを閉じています")
            if self.controller:
                try:
                    self.controller.cleanup()
                except AttributeError:
                    pass
            self.cleanup()
            self.destroy()
    
    def cleanup(self) -> None:
        """リソースクリーンアップ"""
        log.info("メインウィンドウのクリーンアップ実行")
        # 必要に応じてリソースのクリーンアップを行う
        pass