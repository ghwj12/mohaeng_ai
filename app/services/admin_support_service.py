from __future__ import annotations

import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

BASE_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = BASE_DIR / 'data' / 'chatbot'
CONTACTS_PATH = DATA_DIR / 'admin-contacts.json'
LOGS_PATH = DATA_DIR / 'chat-logs.json'


class AdminSupportService:
    def __init__(self) -> None:
        DATA_DIR.mkdir(parents=True, exist_ok=True)

    def _read_json(self, path: Path) -> list[dict[str, Any]]:
        if not path.exists():
            return []
        try:
            payload = json.loads(path.read_text(encoding='utf-8'))
        except Exception:
            return []
        return payload if isinstance(payload, list) else []

    def _write_json(self, path: Path, items: list[dict[str, Any]]) -> None:
        path.write_text(json.dumps(items, ensure_ascii=False, indent=2), encoding='utf-8')

    def _now(self) -> str:
        return datetime.now(timezone.utc).astimezone().isoformat(timespec='seconds')

    def _normalize_status(self, value: Any, *, answer: str = '') -> str:
        text = str(value or '').strip()
        mapping = {
            'RECEIVED': '대기',
            'WAITING': '대기',
            'PENDING': '대기',
            'IN_PROGRESS': '처리중',
            'PROCESSING': '처리중',
            'ANSWERED': '답변완료',
            'DONE': '답변완료',
            'CLOSED': '종결',
        }
        if text in mapping:
            return mapping[text]
        if text in {'대기', '처리중', '답변완료', '종결'}:
            return text
        if answer.strip():
            return '답변완료'
        return '대기'

    def _ensure_session_id(self, item: dict[str, Any]) -> str:
        session_id = str(item.get('sessionId') or item.get('session_id') or '').strip()
        if not session_id:
            session_id = f'auto_{uuid4().hex[:20]}'
            item['sessionId'] = session_id
        return session_id

    def _append_history(self, item: dict[str, Any], action: str, actor: str, changes: dict[str, Any] | None = None) -> None:
        history = item.get('history')
        if not isinstance(history, list):
            history = []
        history.insert(0, {
            'id': uuid4().hex,
            'action': action,
            'actor': actor,
            'createdAt': self._now(),
            'changes': changes or {},
        })
        item['history'] = history[:50]

    def _normalize_contact(self, item: dict[str, Any]) -> dict[str, Any]:
        normalized = dict(item)
        normalized['id'] = str(item.get('id') or item.get('ticketId') or uuid4())
        normalized['content'] = str(item.get('content') or item.get('message') or '').strip()
        normalized['answer'] = str(item.get('answer') or '').strip()
        normalized['status'] = self._normalize_status(item.get('status'), answer=normalized['answer'])
        normalized['sessionId'] = self._ensure_session_id(normalized)
        normalized['source'] = str(item.get('source') or 'chatbot').strip() or 'chatbot'
        normalized['hasAuthorization'] = bool(item.get('hasAuthorization') or item.get('authorization') or item.get('accessToken'))
        normalized['assignee'] = str(item.get('assignee') or '').strip()
        normalized['category'] = str(item.get('category') or '일반').strip() or '일반'
        normalized['priority'] = str(item.get('priority') or '보통').strip() or '보통'
        normalized['createdAt'] = item.get('createdAt') or self._now()
        normalized['answeredAt'] = item.get('answeredAt') or ''
        normalized['updatedAt'] = item.get('updatedAt') or normalized['answeredAt'] or normalized['createdAt']
        history = item.get('history')
        normalized['history'] = history if isinstance(history, list) else []
        return normalized

    def _save_all_contacts(self, items: list[dict[str, Any]]) -> None:
        normalized = [self._normalize_contact(item) for item in items]
        self._write_json(CONTACTS_PATH, normalized)

    def save_contact(self, *, content: str, session_id: str | None = None, authorization: str | None = None, source: str = 'chatbot') -> dict[str, Any]:
        items = self._read_json(CONTACTS_PATH)
        row = {
            'id': str(uuid4()),
            'content': content.strip(),
            'status': '대기',
            'createdAt': self._now(),
            'updatedAt': self._now(),
            'sessionId': (session_id or '').strip() or f'auto_{uuid4().hex[:20]}',
            'hasAuthorization': bool(authorization),
            'source': source,
            'answer': '',
            'assignee': '',
            'category': '회원 문의' if authorization else '일반',
            'priority': '보통',
            'history': [],
        }
        self._append_history(row, '접수', 'AI 챗봇', {'status': '대기'})
        items.insert(0, row)
        self._save_all_contacts(items[:500])
        return row

    def list_contacts(self, *, limit: int = 100) -> list[dict[str, Any]]:
        items = self._read_json(CONTACTS_PATH)
        normalized = [self._normalize_contact(item) for item in items[: max(1, min(limit, 500))]]
        if normalized != items[: len(normalized)]:
            full_items = [self._normalize_contact(item) for item in items]
            self._write_json(CONTACTS_PATH, full_items)
        return normalized

    def update_contact(
        self,
        *,
        item_id: str,
        answer: str | None = None,
        status: str | None = None,
        assignee: str | None = None,
        category: str | None = None,
        priority: str | None = None,
        memo: str | None = None,
        actor: str = '관리자',
    ) -> dict[str, Any] | None:
        items = self._read_json(CONTACTS_PATH)
        updated = None
        for idx, item in enumerate(items):
            current = self._normalize_contact(item)
            item_key = current.get('id') or current.get('ticketId')
            if str(item_key) != str(item_id):
                continue

            changes: dict[str, Any] = {}
            if answer is not None:
                new_answer = str(answer).strip()
                if current.get('answer', '') != new_answer:
                    current['answer'] = new_answer
                    changes['answer'] = True
                    if new_answer:
                        current['answeredAt'] = self._now()
                        if (status or '').strip() in {'', '대기'}:
                            status = '답변완료'
            if status is not None:
                normalized_status = self._normalize_status(status, answer=current.get('answer', ''))
                if current.get('status') != normalized_status:
                    current['status'] = normalized_status
                    changes['status'] = normalized_status
            if assignee is not None:
                new_assignee = str(assignee).strip()
                if current.get('assignee', '') != new_assignee:
                    current['assignee'] = new_assignee
                    changes['assignee'] = new_assignee
            if category is not None:
                new_category = str(category).strip() or '일반'
                if current.get('category', '') != new_category:
                    current['category'] = new_category
                    changes['category'] = new_category
            if priority is not None:
                new_priority = str(priority).strip() or '보통'
                if current.get('priority', '') != new_priority:
                    current['priority'] = new_priority
                    changes['priority'] = new_priority

            current['updatedAt'] = self._now()
            if memo and str(memo).strip():
                changes['memo'] = str(memo).strip()
            self._append_history(current, '수정' if changes else '조회', actor, changes)
            items[idx] = current
            updated = current
            break
        if updated is not None:
            self._save_all_contacts(items)
        return updated

    def answer_contact(self, *, item_id: str, answer: str, status: str = '답변완료', assignee: str | None = None, memo: str | None = None) -> dict[str, Any] | None:
        return self.update_contact(
            item_id=item_id,
            answer=answer,
            status=status,
            assignee=assignee,
            memo=memo,
            actor=assignee or '관리자',
        )

    def delete_contact(self, *, item_id: str) -> dict[str, Any] | None:
        items = self._read_json(CONTACTS_PATH)
        target = None
        remaining: list[dict[str, Any]] = []
        for item in items:
            current = self._normalize_contact(item)
            if str(current.get('id') or current.get('ticketId')) == str(item_id):
                current['updatedAt'] = self._now()
                self._append_history(current, '삭제', '관리자', {})
                target = current
                continue
            remaining.append(current)
        if target is not None:
            self._write_json(CONTACTS_PATH, remaining)
        return target

    def save_log(self, *, question: str, answer: str, intent: str | None = None, session_id: str | None = None, is_error: bool = False) -> dict[str, Any]:
        items = self._read_json(LOGS_PATH)
        row = {
            'id': str(uuid4()),
            'question': question.strip(),
            'answer': answer.strip(),
            'intent': intent or '',
            'createdAt': self._now(),
            'sessionId': session_id or '',
            'isError': bool(is_error),
        }
        items.insert(0, row)
        self._write_json(LOGS_PATH, items[:1000])
        return row

    def list_logs(self, *, limit: int = 150) -> list[dict[str, Any]]:
        return self._read_json(LOGS_PATH)[: max(1, min(limit, 1000))]

    def summarize_logs(self) -> dict[str, Any]:
        items = self._read_json(LOGS_PATH)
        intents = Counter((item.get('intent') or 'unknown') for item in items)
        total = len(items)
        errors = sum(1 for item in items if bool(item.get('isError')))
        return {
            'total': total,
            'errors': errors,
            'topIntents': [{'intent': name, 'count': count} for name, count in intents.most_common(10)],
        }
