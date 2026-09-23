import json
import logging
from pathlib import Path
from typing import Dict, List, Optional

from .models import Question, TestSuite, TestSuiteMeta

logger = logging.getLogger("test_loader")

TESTS_DATA_DIR = Path(__file__).resolve().parent.parent / "tests_data"
DEFAULT_TEST_ID = "test_general_2026"

class TestRepository:
    def __init__(self, data_dir: Path = TESTS_DATA_DIR):
        self.data_dir = data_dir
        self.test_suites: Dict[str, TestSuite] = {}
        self.reload_all_tests()

    def reload_all_tests(self) -> int:
        self.test_suites.clear()

        if not self.data_dir.exists():
            logger.warning(f"Папка с тестами {self.data_dir} не найдена. Создаю папку.")
            self.data_dir.mkdir(parents=True, exist_ok=True)

        json_files = list(self.data_dir.glob("*.json"))
        loaded_count = 0

        for file_path in json_files:
            # Пропускаем шаблоны
            if file_path.name.startswith("template_"):
                continue

            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    raw_data = json.load(f)

                questions_raw = raw_data.get("questions", [])
                total_q = len(questions_raw)

                parsed_questions: List[Question] = []
                for q_dict in questions_raw:
                    parsed_questions.append(Question(**q_dict))

                suite = TestSuite(
                    id=raw_data.get("id", file_path.stem),
                    title=raw_data.get("title", file_path.stem),
                    description=raw_data.get("description", ""),
                    category=raw_data.get("category", "General"),
                    level=raw_data.get("level", "All"),
                    mode=raw_data.get("mode", "fixed"),
                    icon=raw_data.get("icon", "📝"),
                    estimated_time_minutes=raw_data.get("estimated_time_minutes", 5),
                    total_questions=total_q,
                    questions=parsed_questions
                )

                self.test_suites[suite.id] = suite
                loaded_count += 1
                logger.info(f"Загружен тест '{suite.title}' ({suite.id}): {total_q} вопросов.")
            except Exception as e:
                logger.error(f"Ошибка загрузки теста из {file_path.name}: {e}")

        return loaded_count

    def get_default_test_id(self) -> str:
        if DEFAULT_TEST_ID in self.test_suites:
            return DEFAULT_TEST_ID
        if self.test_suites:
            return next(iter(self.test_suites))
        return DEFAULT_TEST_ID

    def get_all_tests_meta(self) -> List[TestSuiteMeta]:
        return [
            TestSuiteMeta(**suite.model_dump(exclude={"questions"}))
            for suite in self.test_suites.values()
        ]

    def get_test_suite(self, test_id: str) -> Optional[TestSuite]:
        return self.test_suites.get(test_id)

    def get_all_questions_pool(self) -> List[Question]:
        pool: Dict[str, Question] = {}
        for suite in self.test_suites.values():
            for q in suite.questions:
                if q.id not in pool:
                    pool[q.id] = q
        return list(pool.values())

test_repository = TestRepository()
