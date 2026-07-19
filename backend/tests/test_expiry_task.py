import asyncio

import pytest

from backend.services import expiry_task


@pytest.mark.asyncio
async def test_vong_lap_goi_runner_lap_lai():
    calls = []

    def runner() -> int:
        calls.append(1)
        return 2

    task = asyncio.create_task(expiry_task._loop(0.01, runner))
    
    # Chờ tối đa 1 giây cho đến khi len(calls) >= 2
    for _ in range(100):
        if len(calls) >= 2:
            break
        await asyncio.sleep(0.01)

    await expiry_task.stop_expiry_task(task)

    assert len(calls) >= 2


@pytest.mark.asyncio
async def test_loi_db_khong_giet_vong_lap():
    calls = []

    def runner() -> int:
        calls.append(1)
        # Lần đầu hỏng; vòng lặp phải chạy tiếp chứ không chết theo.
        if len(calls) == 1:
            raise RuntimeError("mat ket noi database")
        return 0

    task = asyncio.create_task(expiry_task._loop(0.01, runner))
    
    # Chờ tối đa 1 giây cho đến khi len(calls) >= 2
    for _ in range(100):
        if len(calls) >= 2:
            break
        await asyncio.sleep(0.01)

    still_running = not task.done()
    await expiry_task.stop_expiry_task(task)

    assert still_running, "vòng lặp phải sống sót sau lỗi DB"
    assert len(calls) >= 2, "phải thử lại ở chu kỳ sau"


@pytest.mark.asyncio
async def test_stop_huy_duoc_vong_lap():
    task = asyncio.create_task(expiry_task._loop(0.01, lambda: 0))
    await asyncio.sleep(0.02)
    await expiry_task.stop_expiry_task(task)
    assert task.done()


@pytest.mark.asyncio
async def test_stop_chap_nhan_none():
    await expiry_task.stop_expiry_task(None)


def test_tat_qua_config(monkeypatch):
    from backend.config import Settings, get_settings

    get_settings.cache_clear()
    monkeypatch.setenv("RELEASE_EXPIRED_ENABLED", "false")
    try:
        assert Settings().release_expired_enabled is False
    finally:
        get_settings.cache_clear()
