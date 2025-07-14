"""Initial schema creation

Revision ID: 001_initial_schema
Revises: 
Create Date: 2025-07-14 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '001_initial_schema'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ファイル管理テーブル
    op.create_table(
        'files',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('filename', sa.Text(), nullable=False),
        sa.Column('original_name', sa.Text()),
        sa.Column('file_path', sa.Text(), nullable=False),
        sa.Column('collection', sa.Text()),
        sa.Column('file_type', sa.Text()),  # image, flashcard, text, etc.
        sa.Column('file_size', sa.Integer()),
        sa.Column('hash', sa.Text(), unique=True),
        sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP'))
    )
    
    # 画像固有情報テーブル
    op.create_table(
        'images',
        sa.Column('file_id', sa.Integer(), primary_key=True),  # files.idと1対1
        sa.Column('image_type', sa.Text()),
        sa.Column('region_index', sa.Integer()),
        sa.Column('parent_image_id', sa.Integer()),
        sa.Column('mask_image_id', sa.Integer()),
        sa.Column('width', sa.Integer()),
        sa.Column('height', sa.Integer()),
        sa.Column('format', sa.Text()),
        sa.Column('thumbnail_path', sa.Text()),
        sa.ForeignKeyConstraint(['file_id'], ['files.id'], ondelete='CASCADE')
    )
    
    # フラッシュカード固有情報テーブル
    op.create_table(
        'flashcards',
        sa.Column('file_id', sa.Integer(), primary_key=True),  # files.idと1対1
        sa.Column('encoding', sa.Text(), server_default='utf-8'),
        sa.ForeignKeyConstraint(['file_id'], ['files.id'], ondelete='CASCADE')
    )
    
    # LLM出力管理テーブル
    op.create_table(
        'llm_outputs',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('files_num', sa.Integer()),     # LLM_filesで関連するfileの数
        sa.Column('prompt', sa.Text()),           # プロンプト内容
        sa.Column('output', sa.Text()),           # LLMの出力
        sa.Column('model_name', sa.Text()),       # 使用モデル
        sa.Column('params', sa.Text()),           # JSON形式でパラメータ
        sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP'))
    )
    
    # LLM出力とファイルの関連テーブル（多対多）
    op.create_table(
        'llm_files',
        sa.Column('llm_output_id', sa.Integer()),  # llm_outputs.idへの参照
        sa.Column('file_id', sa.Integer()),        # files.idへの参照
        sa.PrimaryKeyConstraint('llm_output_id', 'file_id'),
        sa.ForeignKeyConstraint(['llm_output_id'], ['llm_outputs.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['file_id'], ['files.id'], ondelete='CASCADE')
    )
    
    # インデックスの追加（パフォーマンス向上）
    op.create_index('idx_files_hash', 'files', ['hash'])
    op.create_index('idx_files_file_type', 'files', ['file_type'])
    op.create_index('idx_files_collection', 'files', ['collection'])
    op.create_index('idx_llm_outputs_created_at', 'llm_outputs', ['created_at'])
    op.create_index('idx_llm_files_file_id', 'llm_files', ['file_id'])


def downgrade():
    # インデックスの削除
    op.drop_index('idx_llm_files_file_id', table_name='llm_files')
    op.drop_index('idx_llm_outputs_created_at', table_name='llm_outputs')
    op.drop_index('idx_files_collection', table_name='files')
    op.drop_index('idx_files_file_type', table_name='files')
    op.drop_index('idx_files_hash', table_name='files')
    
    # テーブルの削除（外部キー制約の関係で逆順）
    op.drop_table('llm_files')
    op.drop_table('llm_outputs')
    op.drop_table('flashcards')
    op.drop_table('images')
    op.drop_table('files')