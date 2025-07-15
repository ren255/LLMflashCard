from app.config.logging_config import setup_logging
from app.database import get_engine, get_session
from sqlalchemy.exc import SQLAlchemyError

from app.models import *
from datetime import datetime, timedelta

logger = setup_logging()
# データベース接続
engine = get_engine()
session = get_session()

logger.info("Database connection established")

# ========== 追加（CREATE） ==========

# 簡潔：基本的なファイル追加


def add_file_simple():
    """基本的なファイル追加"""
    logger.info("Starting simple file addition")

    try:
        file = File(
            filename='sample.jpg',
            original_name='sample.jpg',
            file_path='/uploads/sample.jpg',
            file_type='image'
        )
        session.add(file)
        session.commit()

        logger.info(f"File added successfully with ID: {file.id}")
        return file.id

    except SQLAlchemyError as e:
        logger.error(f"Database error during file addition: {str(e)}")
        session.rollback()
        raise
    except Exception as e:
        logger.error(f"Unexpected error during file addition: {str(e)}")
        session.rollback()
        raise

# 応用：画像ファイルと関連情報を同時追加


def add_image_with_details():
    """画像ファイルと関連情報を同時追加"""
    logger.info("Starting image addition with details")

    try:
        # ファイル情報
        file = File(
            filename='photo_001.jpg',
            original_name='vacation_photo.jpg',
            file_path='/uploads/photo_001.jpg',
            collection='vacation2024',
            file_type='image',
            file_size=1024000,
            hash='abc123def456'
        )
        session.add(file)
        session.flush()  # IDを取得するため

        logger.debug(f"File record created with ID: {file.id}")

        # 画像詳細情報
        image = Image(
            file_id=file.id,
            image_type='photo',
            width=1920,
            height=1080,
            format='JPEG',
            thumbnail_path='/thumbnails/photo_001_thumb.jpg'
        )
        session.add(image)
        session.commit()

        logger.info(
            f"Image with details added successfully. File ID: {file.id}, Size: {file.file_size} bytes")
        return file.id

    except SQLAlchemyError as e:
        logger.error(f"Database error during image addition: {str(e)}")
        session.rollback()
        raise
    except Exception as e:
        logger.error(f"Unexpected error during image addition: {str(e)}")
        session.rollback()
        raise

# ========== 更新（UPDATE） ==========

# 簡潔：ファイル名変更


def update_filename(file_id, new_filename):
    """ファイル名を更新"""
    logger.info(f"Updating filename for file ID: {file_id} to: {new_filename}")

    try:
        file = session.query(File).filter(File.id == file_id).first()
        if file:
            old_filename = file.filename
            file.filename = new_filename
            session.commit()

            logger.info(
                f"Filename updated successfully: {old_filename} -> {new_filename}")
            return True
        else:
            logger.warning(
                f"File with ID {file_id} not found for filename update")
            return False

    except SQLAlchemyError as e:
        logger.error(f"Database error during filename update: {str(e)}")
        session.rollback()
        raise
    except Exception as e:
        logger.error(f"Unexpected error during filename update: {str(e)}")
        session.rollback()
        raise

# 応用：複数条件での一括更新


def update_collection_files(old_collection, new_collection):
    """コレクション名を一括更新"""
    logger.info(
        f"Bulk updating collection: {old_collection} -> {new_collection}")

    try:
        updated_count = session.query(File).filter(
            File.collection == old_collection,
            File.file_type == 'image'
        ).update({
            File.collection: new_collection
        })
        session.commit()

        logger.info(
            f"Collection updated successfully. {updated_count} files affected")
        return updated_count

    except SQLAlchemyError as e:
        logger.error(f"Database error during collection update: {str(e)}")
        session.rollback()
        raise
    except Exception as e:
        logger.error(f"Unexpected error during collection update: {str(e)}")
        session.rollback()
        raise

# ========== 検索（READ） ==========

# 簡潔：ID検索


def get_file_by_id(file_id):
    """IDでファイルを検索"""
    logger.debug(f"Searching for file with ID: {file_id}")

    try:
        file = session.query(File).filter(File.id == file_id).first()
        if file:
            logger.debug(f"File found: {file.filename}")
        else:
            logger.warning(f"File with ID {file_id} not found")
        return file

    except SQLAlchemyError as e:
        logger.error(f"Database error during file search: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error during file search: {str(e)}")
        raise

# 応用：複雑な条件での検索とJOIN


def search_images_with_details(collection=None, min_width=None):
    """複雑な条件での画像検索"""
    logger.info(
        f"Searching images with conditions - collection: {collection}, min_width: {min_width}")

    try:
        query = session.query(File, Image).join(
            Image, File.id == Image.file_id)

        if collection:
            query = query.filter(File.collection == collection)
            logger.debug(f"Added collection filter: {collection}")

        if min_width:
            query = query.filter(Image.width >= min_width)
            logger.debug(f"Added min_width filter: {min_width}")

        # 作成日順でソート
        query = query.order_by(File.created_at.desc())

        results = []
        for file, image in query.all():
            results.append({
                'file_id': file.id,
                'filename': file.filename,
                'collection': file.collection,
                'width': image.width,
                'height': image.height,
                'created_at': file.created_at
            })

        logger.info(f"Image search completed. Found {len(results)} results")
        return results

    except SQLAlchemyError as e:
        logger.error(f"Database error during image search: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error during image search: {str(e)}")
        raise

# ========== 削除（DELETE） ==========

# 簡潔：ID指定削除


def delete_file(file_id):
    """IDでファイルを削除"""
    logger.info(f"Deleting file with ID: {file_id}")

    try:
        file = session.query(File).filter(File.id == file_id).first()
        if file:
            filename = file.filename
            session.delete(file)
            session.commit()

            logger.info(
                f"File deleted successfully: {filename} (ID: {file_id})")
            return True
        else:
            logger.warning(f"File with ID {file_id} not found for deletion")
            return False

    except SQLAlchemyError as e:
        logger.error(f"Database error during file deletion: {str(e)}")
        session.rollback()
        raise
    except Exception as e:
        logger.error(f"Unexpected error during file deletion: {str(e)}")
        session.rollback()
        raise

# 応用：条件指定での一括削除


def cleanup_old_temp_files(days_old=30):
    """古い一時ファイルのクリーンアップ"""
    logger.info(f"Starting cleanup of temp files older than {days_old} days")

    try:
        cutoff_date = datetime.now() - timedelta(days=days_old)
        logger.debug(f"Cutoff date: {cutoff_date}")

        # 一時ファイルを削除（collectionが'temp'で古いもの）
        deleted_count = session.query(File).filter(
            File.collection == 'temp',
            File.created_at < cutoff_date
        ).delete()

        session.commit()

        logger.info(f"Cleanup completed. {deleted_count} temp files deleted")
        return deleted_count

    except SQLAlchemyError as e:
        logger.error(f"Database error during cleanup: {str(e)}")
        session.rollback()
        raise
    except Exception as e:
        logger.error(f"Unexpected error during cleanup: {str(e)}")
        session.rollback()
        raise

# ========== 使用例 ==========


if __name__ == "__main__":
    logger.info("Starting database operations example")

    try:
        # 追加
        file_id = add_file_simple()
        logger.info(f"追加されたファイルID: {file_id}")

        # 検索
        file = get_file_by_id(file_id)
        if file:
            logger.info(f"検索結果: {file.filename}")

        # 更新
        update_result = update_filename(file_id, "updated_sample.jpg")
        if update_result:
            logger.info("ファイル名更新成功")

        # 削除
        delete_result = delete_file(file_id)
        if delete_result:
            logger.info("ファイル削除成功")

        # クリーンアップ例
        cleanup_count = cleanup_old_temp_files(30)
        logger.info(f"クリーンアップ完了: {cleanup_count}件削除")

    except Exception as e:
        logger.error(f"Example execution failed: {str(e)}")
    finally:
        # セッションクローズ
        session.close()
        logger.info("Database session closed")
