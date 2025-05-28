"""
プロジェクト固有のカスタムウィジェット
LLMflashCardで使用する専用コンポーネント
"""

import customtkinter as ctk
from tkinter import ttk
from typing import Callable, Optional, List, Dict, Any
from PIL import Image, ImageTk
from pathlib import Path
from utils import log


class ImagePreviewWidget(ctk.CTkFrame):
    """画像プレビュー用ウィジェット"""
    
    def __init__(self, parent, width: int = 200, height: int = 200, **kwargs):
        super().__init__(parent, **kwargs)
        
        self.width = width
        self.height = height
        self.current_image = None
        self.current_path = None
        
        self.setup_ui()
    
    def setup_ui(self):
        """UI構築"""
        # プレビューラベル
        self.preview_label = ctk.CTkLabel(
            self,
            text="画像なし",
            width=self.width,
            height=self.height,
            fg_color="gray80"
        )
        self.preview_label.pack(fill="both", expand=True, padx=5, pady=5)
    
    def load_image(self, image_path: str | Path):
        """画像を読み込んでプレビュー表示"""
        try:
            image_path = Path(image_path)
            if not image_path.exists():
                self.show_no_image("ファイルが見つかりません")
                return False
            
            # 画像読み込み
            image = Image.open(image_path)
            
            # リサイズ（アスペクト比維持）
            image.thumbnail((self.width - 10, self.height - 10), Image.Resampling.LANCZOS)
            
            # PhotoImageに変換
            photo = ImageTk.PhotoImage(image)
            
            # ラベルに設定
            self.preview_label.configure(
                image=photo,
                text="",
                fg_color="transparent"
            )
            
            # 参照を保持（GC対策）
            self.current_image = photo
            self.current_path = image_path
            
            log.info(f"Image loaded in preview: {image_path}")
            return True
            
        except Exception as e:
            log.error(f"Failed to load image: {e}")
            self.show_no_image("画像読み込み失敗")
            return False
    
    def show_no_image(self, message: str = "画像なし"):
        """画像なし状態を表示"""
        self.preview_label.configure(
            image="",
            text=message,
            fg_color="gray80"
        )
        self.current_image = None
        self.current_path = None
    
    def clear(self):
        """プレビューをクリア"""
        self.show_no_image()


class FlashcardPreviewWidget(ctk.CTkFrame):
    """フラッシュカードプレビュー用ウィジェット"""
    
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        
        self.current_data = None
        self.setup_ui()
    
    def setup_ui(self):
        """UI構築"""
        # タイトル
        self.title_label = ctk.CTkLabel(
            self,
            text="フラッシュカードプレビュー",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        self.title_label.pack(pady=(10, 5))
        
        # 情報表示エリア
        self.info_frame = ctk.CTkFrame(self)
        self.info_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        # 詳細テキストエリア
        self.detail_text = ctk.CTkTextbox(
            self.info_frame,
            height=150,
            wrap="word"
        )
        self.detail_text.pack(fill="both", expand=True, padx=5, pady=5)
    
    def load_flashcard_data(self, data: Dict[str, Any]):
        """フラッシュカードデータを表示"""
        try:
            self.current_data = data
            
            # テキストエリアをクリア
            self.detail_text.delete("1.0", "end")
            
            # データを整形して表示
            info_text = []
            info_text.append(f"ファイル名: {data.get('filename', '不明')}")
            info_text.append(f"元ファイル名: {data.get('original_name', '不明')}")
            info_text.append(f"作成日時: {data.get('created_at', '不明')}")
            info_text.append(f"行数: {data.get('row_count', 0)}行")
            info_text.append(f"エンコーディング: {data.get('encoding', 'utf-8')}")
            info_text.append(f"区切り文字: {data.get('delimiter', ',')}")
            
            if data.get('columns'):
                columns = data['columns'].split(',') if isinstance(data['columns'], str) else data['columns']
                info_text.append(f"列数: {len(columns)}列")
                info_text.append("列名:")
                for i, col in enumerate(columns[:10]):  # 最初の10列まで表示
                    info_text.append(f"  {i+1}. {col.strip()}")
                if len(columns) > 10:
                    info_text.append(f"  ... 他{len(columns)-10}列")
            
            self.detail_text.insert("1.0", "\n".join(info_text))
            
            log.info(f"Flashcard data loaded in preview: {data.get('filename')}")
            
        except Exception as e:
            log.error(f"Failed to load flashcard data: {e}")
            self.show_no_data("データ読み込み失敗")
    
    def show_no_data(self, message: str = "データなし"):
        """データなし状態を表示"""
        self.detail_text.delete("1.0", "end")
        self.detail_text.insert("1.0", message)
        self.current_data = None
    
    def clear(self):
        """プレビューをクリア"""
        self.show_no_data()


class SearchWidget(ctk.CTkFrame):
    """検索用ウィジェット"""
    
    def __init__(self, parent, on_search: Callable[[str], None], placeholder: str = "検索...", **kwargs):
        super().__init__(parent, **kwargs)
        
        self.on_search = on_search
        self.placeholder = placeholder
        self.setup_ui()
    
    def setup_ui(self):
        """UI構築"""
        # 検索エントリー
        self.search_entry = ctk.CTkEntry(
            self,
            placeholder_text=self.placeholder,
            height=32
        )
        self.search_entry.pack(side="left", fill="x", expand=True, padx=(0, 5))
        
        # 検索ボタン
        self.search_button = ctk.CTkButton(
            self,
            text="🔍",
            width=32,
            height=32,
            command=self.perform_search
        )
        self.search_button.pack(side="right")
        
        # Enterキーバインド
        self.search_entry.bind("<Return>", lambda e: self.perform_search())
    
    def perform_search(self):
        """検索実行"""
        query = self.search_entry.get().strip()
        if self.on_search:
            self.on_search(query)
        log.info(f"Search performed: {query}")
    
    def clear(self):
        """検索欄をクリア"""
        self.search_entry.delete(0, "end")
    
    def set_text(self, text: str):
        """検索欄にテキストを設定"""
        self.search_entry.delete(0, "end")
        self.search_entry.insert(0, text)


class StatusBar(ctk.CTkFrame):
    """ステータスバー"""
    
    def __init__(self, parent, **kwargs):
        super().__init__(parent, height=30, **kwargs)
        
        self.pack_propagate(False)
        self.setup_ui()
    
    def setup_ui(self):
        """UI構築"""
        # ステータステキスト
        self.status_label = ctk.CTkLabel(
            self,
            text="準備完了",
            anchor="w"
        )
        self.status_label.pack(side="left", fill="x", expand=True, padx=10)
        
        # 右側情報（件数など）
        self.info_label = ctk.CTkLabel(
            self,
            text="",
            anchor="e"
        )
        self.info_label.pack(side="right", padx=10)
    
    def set_status(self, message: str):
        """ステータスメッセージを設定"""
        self.status_label.configure(text=message)
        log.info(f"Status: {message}")
    
    def set_info(self, info: str):
        """右側情報を設定"""
        self.info_label.configure(text=info)
    
    def clear(self):
        """ステータスをクリア"""
        self.status_label.configure(text="準備完了")
        self.info_label.configure(text="")


class ProgressDialog(ctk.CTkToplevel):
    """進捗ダイアログ"""
    
    def __init__(self, parent, title: str = "処理中...", message: str = "しばらくお待ちください", **kwargs):
        super().__init__(parent, **kwargs)
        
        self.title(title)
        self.geometry("400x150")
        self.resizable(False, False)
        
        # 中央配置
        self.center_window()
        
        # モーダル設定
        self.transient(parent)
        self.grab_set()
        
        self.setup_ui(message)
    
    def center_window(self):
        """ウィンドウを中央配置"""
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f"{width}x{height}+{x}+{y}")
    
    def setup_ui(self, message: str):
        """UI構築"""
        # メッセージ
        self.message_label = ctk.CTkLabel(
            self,
            text=message,
            font=ctk.CTkFont(size=14)
        )
        self.message_label.pack(pady=(20, 10))
        
        # プログレスバー
        self.progress_bar = ctk.CTkProgressBar(self, width=300)
        self.progress_bar.pack(pady=10)
        self.progress_bar.set(0)
        
        # 進捗テキスト
        self.progress_text = ctk.CTkLabel(self, text="0%")
        self.progress_text.pack(pady=(0, 20))
    
    def update_progress(self, value: float, text: str = ""):
        """進捗を更新（0.0-1.0）"""
        self.progress_bar.set(value)
        if text:
            self.progress_text.configure(text=text)
        else:
            self.progress_text.configure(text=f"{int(value*100)}%")
        self.update()
    
    def set_message(self, message: str):
        """メッセージを更新"""
        self.message_label.configure(text=message)
        self.update()
    
    def close_dialog(self):
        """ダイアログを閉じる"""
        self.grab_release()
        self.destroy()