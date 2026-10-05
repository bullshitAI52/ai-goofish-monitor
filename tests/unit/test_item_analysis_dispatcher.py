import asyncio

from src.services.item_analysis_dispatcher import (
    ItemAnalysisDispatcher,
    ItemAnalysisJob,
)


def test_item_analysis_dispatcher_uses_bounded_concurrency():
    active_ai_calls = 0
    max_active_ai_calls = 0
    saved_records = []
    notifications = []

    async def seller_loader(user_id: str):
        await asyncio.sleep(0.005)
        return {"卖家ID": user_id}

    async def image_downloader(product_id: str, image_urls: list[str], task_name: str):
        return []

    async def ai_analyzer(record: dict, image_paths: list[str], prompt_text: str):
        nonlocal active_ai_calls, max_active_ai_calls
        active_ai_calls += 1
        max_active_ai_calls = max(max_active_ai_calls, active_ai_calls)
        await asyncio.sleep(0.03)
        active_ai_calls -= 1
        return {
            "analysis_source": "ai",
            "is_recommended": True,
            "reason": f"推荐 {record['商品信息']['商品ID']}",
            "keyword_hit_count": 0,
        }

    async def notifier(item_data: dict, reason: str):
        notifications.append((item_data["商品ID"], reason))

    async def saver(record: dict, keyword: str):
        saved_records.append((keyword, record))
        return True

    async def run():
        dispatcher = ItemAnalysisDispatcher(
            concurrency=2,
            skip_ai_analysis=False,
            seller_loader=seller_loader,
            image_downloader=image_downloader,
            ai_analyzer=ai_analyzer,
            notifier=notifier,
            saver=saver,
        )
        for index in range(3):
            dispatcher.submit(
                ItemAnalysisJob(
                    keyword="demo",
                    task_name="Demo",
                    decision_mode="ai",
                    analyze_images=False,
                    prompt_text="prompt",
                    keyword_rules=(),
                    final_record={
                        "商品信息": {"商品ID": str(index), "商品图片列表": []},
                        "卖家信息": {},
                    },
                    seller_id=f"seller-{index}",
                    zhima_credit_text="优秀",
                    registration_duration_text="来闲鱼1年",
                )
            )
        await dispatcher.join()
        return dispatcher

    dispatcher = asyncio.run(run())
    assert dispatcher.completed_count == 3
    assert len(saved_records) == 3
    assert len(notifications) == 3
    assert max_active_ai_calls == 2
    assert saved_records[0][1]["卖家信息"]["卖家ID"].startswith("seller-")


def test_item_analysis_dispatcher_supports_keyword_mode_without_ai():
    saved_records = []

    async def seller_loader(user_id: str):
        return {"卖家标签": "个人闲置"}

    async def image_downloader(product_id: str, image_urls: list[str], task_name: str):
        raise AssertionError("关键词模式不应下载图片")

    async def ai_analyzer(record: dict, image_paths: list[str], prompt_text: str):
        raise AssertionError("关键词模式不应调用 AI")

    async def notifier(item_data: dict, reason: str):
        return None

    async def saver(record: dict, keyword: str):
        saved_records.append(record)
        return True

    async def run():
        dispatcher = ItemAnalysisDispatcher(
            concurrency=1,
            skip_ai_analysis=False,
            seller_loader=seller_loader,
            image_downloader=image_downloader,
            ai_analyzer=ai_analyzer,
            notifier=notifier,
            saver=saver,
        )
        dispatcher.submit(
            ItemAnalysisJob(
                keyword="demo",
                task_name="Demo",
                decision_mode="keyword",
                analyze_images=False,
                prompt_text="",
                keyword_rules=("个人闲置",),
                final_record={
                    "商品信息": {"商品ID": "1", "商品标题": "演示商品"},
                    "卖家信息": {},
                },
                seller_id="seller-1",
                zhima_credit_text="优秀",
                registration_duration_text="来闲鱼1年",
            )
        )
        await dispatcher.join()

    asyncio.run(run())
    assert saved_records[0]["ai_analysis"]["analysis_source"] == "keyword"
    assert saved_records[0]["ai_analysis"]["is_recommended"] is True


def test_failed_save_is_reported_after_other_jobs_finish():
    import pytest

    async def run(fail_early, raises):
        notifications = []
        saved = []

        async def unused(*args):
            return {}

        async def saver(record, keyword):
            item_id = record['商品信息']['商品ID']
            if item_id == 'bad':
                if raises:
                    raise OSError('disk full')
                return False
            await asyncio.sleep(0.01)
            saved.append(item_id)
            return True

        async def notifier(item, reason):
            notifications.append(item['商品ID'])

        dispatcher = ItemAnalysisDispatcher(
            concurrency=2, skip_ai_analysis=True, seller_loader=unused,
            image_downloader=unused, ai_analyzer=unused, notifier=notifier, saver=saver,
        )
        for item_id in ('bad', 'good'):
            dispatcher.submit(ItemAnalysisJob(
                keyword='demo', task_name='demo', decision_mode='ai',
                analyze_images=False, prompt_text='', keyword_rules=(),
                final_record={'商品信息': {'商品ID': item_id}}, seller_id=None,
                zhima_credit_text=None, registration_duration_text='',
            ))
        if fail_early:
            await asyncio.sleep(0.03)
        with pytest.raises(OSError if raises else RuntimeError):
            await dispatcher.join()
        assert saved == ['good']
        assert notifications == ['good']
        assert dispatcher.completed_count == 1
        assert not dispatcher._tasks

    for fail_early in (False, True):
        for raises in (False, True):
            asyncio.run(run(fail_early, raises))
