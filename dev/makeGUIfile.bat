@echo off
REM ルートディレクトリ作成
cd gui

REM サブディレクトリ作成
mkdir components\common
mkdir components\flashcard
mkdir components\image
mkdir controllers
mkdir views
mkdir styles
mkdir utils

REM 空ファイル作成
type nul > __init__.py

type nul > components\__init__.py
type nul > components\common\__init__.py
type nul > components\common\base_window.py
type nul > components\common\custom_widgets.py
type nul > components\common\dialogs.py

type nul > components\flashcard\__init__.py
type nul > components\flashcard\flashcard_list_view.py
type nul > components\flashcard\flashcard_detail_view.py
type nul > components\flashcard\flashcard_edit_dialog.py
type nul > components\flashcard\csv_import_dialog.py

type nul > components\image\__init__.py
type nul > components\image\image_gallery.py
type nul > components\image\image_viewer.py
type nul > components\image\image_edit_tools.py
type nul > components\image\mask_editor.py

type nul > controllers\__init__.py
type nul > controllers\main_controller.py
type nul > controllers\flashcard_controller.py
type nul > controllers\image_controller.py

type nul > views\__init__.py
type nul > views\main_window.py
type nul > views\flashcard_manager.py
type nul > views\image_manager.py

type nul > styles\__init__.py
type nul > styles\themes.py
type nul > styles\colors.py

type nul > utils\__init__.py
type nul > utils\gui_helpers.py
type nul > utils\validators.py

echo ディレクトリ構造とファイルの作成が完了しました。
pause
