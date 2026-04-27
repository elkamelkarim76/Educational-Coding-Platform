"""add chat tables
Revision ID: a1b2c3d4e5f6
Revises: f0ef164081cd
Create Date: 2026-04-20 10:00:00
"""
from alembic import op
import sqlalchemy as sa

revision = 'a1b2c3d4e5f6'
down_revision = '787cb8d1b77c'
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.create_table('chat_room',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('exercise_id', sa.Integer(), sa.ForeignKey('exercise.id', ondelete='CASCADE'), nullable=False, unique=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_table('chat_message',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('room_id', sa.Integer(), sa.ForeignKey('chat_room.id', ondelete='CASCADE'), nullable=False),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('user.id', ondelete='CASCADE'), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('sent_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('ix_chat_message_room_id', 'chat_message', ['room_id'])

def downgrade() -> None:
    op.drop_index('ix_chat_message_room_id', table_name='chat_message')
    op.drop_table('chat_message')
    op.drop_table('chat_room')
