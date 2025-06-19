#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库模型和服务
用于管理对话历史存储
"""

import sqlite3
import json
import uuid
from datetime import datetime
from typing import List, Dict, Optional, Tuple
import logging

logger = logging.getLogger(__name__)

class ChatDatabase:
    def __init__(self, db_path: str = "chat_history.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """初始化数据库表"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 创建对话会话表
                cursor.execute('''
                CREATE TABLE IF NOT EXISTS chat_sessions (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    message_count INTEGER DEFAULT 0,
                    model TEXT,
                    is_archived BOOLEAN DEFAULT FALSE
                )
                ''')
                
                # 创建消息表
                cursor.execute('''
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    content_type TEXT DEFAULT 'text',
                    image_data TEXT,
                    model TEXT,
                    provider TEXT,
                    file_name TEXT,
                    file_size INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (session_id) REFERENCES chat_sessions (id) ON DELETE CASCADE
                )
                ''')
                
                # 创建索引
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_messages_session_id ON messages(session_id)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_sessions_created_at ON chat_sessions(created_at DESC)')
                
                conn.commit()
                logger.info("数据库初始化完成")
                
        except Exception as e:
            logger.error(f"数据库初始化失败: {e}")
            raise
    
    def create_session(self, title: str = None, model: str = None) -> str:
        """创建新的对话会话"""
        try:
            session_id = str(uuid.uuid4())
            if not title:
                title = f"对话 {datetime.now().strftime('%Y-%m-%d %H:%M')}"
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                INSERT INTO chat_sessions (id, title, model, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?)
                ''', (session_id, title, model, datetime.now(), datetime.now()))
                conn.commit()
                
            logger.info(f"创建新对话会话: {session_id}")
            return session_id
            
        except Exception as e:
            logger.error(f"创建会话失败: {e}")
            raise
    
    def get_sessions(self, limit: int = 50, offset: int = 0) -> List[Dict]:
        """获取对话会话列表"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                SELECT id, title, created_at, updated_at, message_count, model, is_archived
                FROM chat_sessions
                WHERE is_archived = FALSE
                ORDER BY updated_at DESC
                LIMIT ? OFFSET ?
                ''', (limit, offset))
                
                sessions = []
                for row in cursor.fetchall():
                    sessions.append({
                        'id': row[0],
                        'title': row[1],
                        'created_at': row[2],
                        'updated_at': row[3],
                        'message_count': row[4],
                        'model': row[5],
                        'is_archived': bool(row[6])
                    })
                
                return sessions
                
        except Exception as e:
            logger.error(f"获取会话列表失败: {e}")
            return []
    
    def get_session_by_id(self, session_id: str) -> Optional[Dict]:
        """根据ID获取对话会话"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                SELECT id, title, created_at, updated_at, message_count, model, is_archived
                FROM chat_sessions
                WHERE id = ?
                ''', (session_id,))
                
                row = cursor.fetchone()
                if row:
                    return {
                        'id': row[0],
                        'title': row[1],
                        'created_at': row[2],
                        'updated_at': row[3],
                        'message_count': row[4],
                        'model': row[5],
                        'is_archived': bool(row[6])
                    }
                return None
                
        except Exception as e:
            logger.error(f"获取会话失败: {e}")
            return None
    
    def update_session_title(self, session_id: str, title: str) -> bool:
        """更新会话标题"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                UPDATE chat_sessions
                SET title = ?, updated_at = ?
                WHERE id = ?
                ''', (title, datetime.now(), session_id))
                
                if cursor.rowcount > 0:
                    conn.commit()
                    return True
                return False
                
        except Exception as e:
            logger.error(f"更新会话标题失败: {e}")
            return False
    
    def delete_session(self, session_id: str) -> bool:
        """删除对话会话"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                # 删除会话（消息会因为外键约束自动删除）
                cursor.execute('DELETE FROM chat_sessions WHERE id = ?', (session_id,))
                
                if cursor.rowcount > 0:
                    conn.commit()
                    logger.info(f"删除会话: {session_id}")
                    return True
                return False
                
        except Exception as e:
            logger.error(f"删除会话失败: {e}")
            return False
    
    def archive_session(self, session_id: str) -> bool:
        """归档对话会话"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                UPDATE chat_sessions
                SET is_archived = TRUE, updated_at = ?
                WHERE id = ?
                ''', (datetime.now(), session_id))
                
                if cursor.rowcount > 0:
                    conn.commit()
                    return True
                return False
                
        except Exception as e:
            logger.error(f"归档会话失败: {e}")
            return False
    
    def add_message(self, session_id: str, role: str, content: str, 
                   content_type: str = 'text', image_data: str = None,
                   model: str = None, provider: str = None,
                   file_name: str = None, file_size: int = None) -> bool:
        """添加消息到会话"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 插入消息
                cursor.execute('''
                INSERT INTO messages (session_id, role, content, content_type, image_data, model, provider, file_name, file_size)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (session_id, role, content, content_type, image_data, model, provider, file_name, file_size))
                
                # 更新会话的消息计数和更新时间
                cursor.execute('''
                UPDATE chat_sessions
                SET message_count = message_count + 1, updated_at = ?
                WHERE id = ?
                ''', (datetime.now(), session_id))
                
                conn.commit()
                return True
                
        except Exception as e:
            logger.error(f"添加消息失败: {e}")
            return False
    
    def get_messages(self, session_id: str, limit: int = 100, offset: int = 0) -> List[Dict]:
        """获取会话的消息列表"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                SELECT id, role, content, content_type, image_data, model, provider, file_name, file_size, created_at
                FROM messages
                WHERE session_id = ?
                ORDER BY created_at ASC
                LIMIT ? OFFSET ?
                ''', (session_id, limit, offset))
                
                messages = []
                for row in cursor.fetchall():
                    message = {
                        'id': row[0],
                        'role': row[1],
                        'content': row[2],
                        'content_type': row[3],
                        'image_data': row[4],
                        'model': row[5],
                        'provider': row[6],
                        'file_name': row[7],
                        'file_size': row[8],
                        'created_at': row[9]
                    }
                    messages.append(message)
                
                return messages
                
        except Exception as e:
            logger.error(f"获取消息列表失败: {e}")
            return []
    
    def get_message_count(self, session_id: str) -> int:
        """获取会话的消息数量"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT COUNT(*) FROM messages WHERE session_id = ?', (session_id,))
                return cursor.fetchone()[0]
                
        except Exception as e:
            logger.error(f"获取消息数量失败: {e}")
            return 0
    
    def search_messages(self, query: str, session_id: str = None, limit: int = 50) -> List[Dict]:
        """搜索消息"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                if session_id:
                    cursor.execute('''
                    SELECT m.id, m.session_id, m.role, m.content, m.content_type, 
                           m.image_data, m.model, m.provider, m.created_at, s.title
                    FROM messages m
                    JOIN chat_sessions s ON m.session_id = s.id
                    WHERE m.session_id = ? AND m.content LIKE ?
                    ORDER BY m.created_at DESC
                    LIMIT ?
                    ''', (session_id, f'%{query}%', limit))
                else:
                    cursor.execute('''
                    SELECT m.id, m.session_id, m.role, m.content, m.content_type, 
                           m.image_data, m.model, m.provider, m.created_at, s.title
                    FROM messages m
                    JOIN chat_sessions s ON m.session_id = s.id
                    WHERE m.content LIKE ?
                    ORDER BY m.created_at DESC
                    LIMIT ?
                    ''', (f'%{query}%', limit))
                
                messages = []
                for row in cursor.fetchall():
                    message = {
                        'id': row[0],
                        'session_id': row[1],
                        'role': row[2],
                        'content': row[3],
                        'content_type': row[4],
                        'image_data': row[5],
                        'model': row[6],
                        'provider': row[7],
                        'created_at': row[8],
                        'session_title': row[9]
                    }
                    messages.append(message)
                
                return messages
                
        except Exception as e:
            logger.error(f"搜索消息失败: {e}")
            return []
    
    def get_statistics(self) -> Dict:
        """获取统计信息"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 获取会话总数
                cursor.execute('SELECT COUNT(*) FROM chat_sessions WHERE is_archived = FALSE')
                total_sessions = cursor.fetchone()[0]
                
                # 获取消息总数
                cursor.execute('SELECT COUNT(*) FROM messages')
                total_messages = cursor.fetchone()[0]
                
                # 获取今日新增会话数
                cursor.execute('''
                SELECT COUNT(*) FROM chat_sessions 
                WHERE DATE(created_at) = DATE('now') AND is_archived = FALSE
                ''')
                today_sessions = cursor.fetchone()[0]
                
                # 获取今日新增消息数
                cursor.execute('''
                SELECT COUNT(*) FROM messages 
                WHERE DATE(created_at) = DATE('now')
                ''')
                today_messages = cursor.fetchone()[0]
                
                return {
                    'total_sessions': total_sessions,
                    'total_messages': total_messages,
                    'today_sessions': today_sessions,
                    'today_messages': today_messages
                }
                
        except Exception as e:
            logger.error(f"获取统计信息失败: {e}")
            return {
                'total_sessions': 0,
                'total_messages': 0,
                'today_sessions': 0,
                'today_messages': 0
            } 