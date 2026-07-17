"""Test Khối 2 — DLP bid price, quy tắc chấp nhận + quota, gán ghế, ghép đoạn trống
(ai_service/optimization.py)."""

import random
from types import SimpleNamespace

import numpy as np
import pytest

from ai_service import optimization as opt

# ============================================================
# Lớp A — DLP: ma trận, LP, giải HiGHS, dual, kiểm định
# ============================================================


def test_build_capacity_matrix_rows_and_capacity():
    od_products = [
        dict(od_id=0, seat_type="ngoi_mem", segments=[0], base_price=100.0),
        dict(od_id=1, seat_type="ngoi_mem", segments=[1], base_price=200.0),
        dict(od_id=2, seat_type="ngoi_mem", segments=[0, 1], base_price=250.0),
    ]
    capacity = {"ngoi_mem": 10, "giuong_nam_k6": 5}

    dlp = opt.build_capacity_matrix(od_products, nseg=2, capacity=capacity)

    assert dlp.A.shape == (4, 3)  # 2 seat_type x 2 seg hàng, 3 OD cột
    assert dlp.constraint_keys == [(0, "ngoi_mem"), (1, "ngoi_mem"), (0, "giuong_nam_k6"), (1, "giuong_nam_k6")]
    np.testing.assert_array_equal(dlp.capacity, [10, 10, 5, 5])
    # seg0/ngoi_mem: od0 (seg0) và od2 (seg0,1) đi qua -> cột [1,0,1]
    np.testing.assert_array_equal(dlp.A[0], [1, 0, 1])
    # seg1/ngoi_mem: od1 và od2 đi qua -> [0,1,1]
    np.testing.assert_array_equal(dlp.A[1], [0, 1, 1])
    # giuong_nam_k6: không OD nào dùng loại chỗ này -> toàn 0
    np.testing.assert_array_equal(dlp.A[2], [0, 0, 0])
    np.testing.assert_array_equal(dlp.A[3], [0, 0, 0])


def test_build_demand_bounds_defaults_missing_od_to_zero_and_clips_negative():
    od_products = [dict(od_id=0), dict(od_id=1), dict(od_id=2)]
    lambda_hat = {0: 5.5, 1: -2.0}  # od 2 không có dự báo

    ub = opt.build_demand_bounds(od_products, lambda_hat)

    np.testing.assert_array_equal(ub, [5.5, 0.0, 0.0])


def test_solve_bid_prices_binding_vs_nonbinding_constraint():
    """seg0 nhu cầu (20) vượt sức chứa (10) -> ràng buộc binding -> bid price > 0.
    seg1 nhu cầu (3) dưới sức chứa (10) -> ràng buộc lỏng (slack) -> bid price = 0."""
    od_products = [
        dict(od_id=0, seat_type="ngoi_mem", segments=[0], base_price=100.0),
        dict(od_id=1, seat_type="ngoi_mem", segments=[1], base_price=100.0),
    ]
    lambda_hat = {0: 20.0, 1: 3.0}
    capacity = {"ngoi_mem": 10, "giuong_nam_k6": 5}

    sol = opt.solve_bid_prices(od_products, lambda_hat, nseg=2, capacity=capacity)

    assert sol["bid_prices"][(0, "ngoi_mem")] == pytest.approx(100.0)
    assert sol["bid_prices"][(1, "ngoi_mem")] == pytest.approx(0.0)
    assert sol["quotas"][0] == pytest.approx(10.0)
    assert sol["quotas"][1] == pytest.approx(3.0)
    assert sol["revenue_lp"] == pytest.approx(10 * 100.0 + 3 * 100.0)


def test_solve_bid_prices_rejects_od_priced_below_opportunity_cost():
    """Chặng khan hiếm (capacity=5, nhu cầu tổng=15 từ 2 OD) -> OD giá thấp bị đẩy
    quota về 0 để nhường chỗ cho OD giá cao — đúng tinh thần tối đa hóa doanh thu."""
    od_products = [
        dict(od_id=0, seat_type="ngoi_mem", segments=[0], base_price=50.0),  # rẻ
        dict(od_id=1, seat_type="ngoi_mem", segments=[0], base_price=500.0),  # đắt
    ]
    lambda_hat = {0: 10.0, 1: 10.0}
    capacity = {"ngoi_mem": 5, "giuong_nam_k6": 5}

    sol = opt.solve_bid_prices(od_products, lambda_hat, nseg=1, capacity=capacity)

    assert sol["quotas"][1] == pytest.approx(5.0)  # OD đắt chiếm hết capacity
    assert sol["quotas"][0] == pytest.approx(0.0)
    assert sol["accept"][0]["accept"] is False  # giá 50 < bid price (=500)
    assert sol["accept"][1]["accept"] is True


def test_validate_solution_raises_on_capacity_violation():
    A = np.array([[1.0, 1.0]])
    capacity = np.array([1.0])
    ub = np.array([5.0, 5.0])
    res = SimpleNamespace(x=np.array([1.0, 1.0]))  # tổng=2 > capacity=1

    with pytest.raises(RuntimeError, match="sức chứa"):
        opt.validate_solution(res, A, capacity, ub)


def test_validate_solution_raises_on_negative_x():
    A = np.array([[1.0]])
    capacity = np.array([5.0])
    ub = np.array([5.0])
    res = SimpleNamespace(x=np.array([-1.0]))

    with pytest.raises(RuntimeError, match="âm"):
        opt.validate_solution(res, A, capacity, ub)


def test_validate_solution_raises_on_demand_bound_violation():
    A = np.array([[1.0]])
    capacity = np.array([100.0])
    ub = np.array([2.0])
    res = SimpleNamespace(x=np.array([5.0]))  # vượt trần nhu cầu

    with pytest.raises(RuntimeError, match="trần nhu cầu"):
        opt.validate_solution(res, A, capacity, ub)


def test_validate_solution_passes_on_feasible_solution():
    A = np.array([[1.0, 1.0]])
    capacity = np.array([2.0])
    ub = np.array([5.0, 5.0])
    res = SimpleNamespace(x=np.array([1.0, 1.0]))

    opt.validate_solution(res, A, capacity, ub)  # không raise


# ============================================================
# Quy tắc chấp nhận + quota
# ============================================================


def test_check_acceptance_boundary_is_inclusive():
    assert opt.check_acceptance(base_price=100.0, opportunity_cost=90.0) is True
    assert opt.check_acceptance(base_price=100.0, opportunity_cost=100.0) is True  # bằng -> vẫn chấp nhận
    assert opt.check_acceptance(base_price=100.0, opportunity_cost=100.01) is False


def test_compute_accept_decisions_sums_opportunity_cost_across_segments():
    od_products = [
        dict(od_id=0, seat_type="ngoi_mem", segments=[0, 1], base_price=150.0),
        dict(od_id=1, seat_type="ngoi_mem", segments=[0], base_price=40.0),
    ]
    bid_prices = {(0, "ngoi_mem"): 60.0, (1, "ngoi_mem"): 50.0}

    accept = opt.compute_accept_decisions(od_products, bid_prices)

    assert accept[0]["opportunity_cost"] == pytest.approx(110.0)
    assert accept[0]["accept"] is True  # 150 >= 110
    assert accept[1]["opportunity_cost"] == pytest.approx(60.0)
    assert accept[1]["accept"] is False  # 40 < 60


def test_round_quota_floors_true_fractional_value():
    assert opt.round_quota(3.7) == 3


def test_round_quota_corrects_floating_point_noise_near_integer():
    # 2.999999999 lẽ ra là 3 (nhiễu số học của solver), floor trần không có epsilon
    # sẽ sai thành 2.
    assert opt.round_quota(2.999999999) == 3


def test_round_quota_clips_tiny_negative_noise_to_zero():
    assert opt.round_quota(-1e-9) == 0


def test_round_quota_raises_on_real_negative_value():
    with pytest.raises(ValueError):
        opt.round_quota(-0.5)


# ============================================================
# Lớp B — Gán ghế (interval partitioning)
# ============================================================


def test_assign_seats_non_overlapping_bookings_share_one_seat():
    bookings = [
        dict(origin_idx=0, dest_idx=2, seat_type="ngoi_mem"),
        dict(origin_idx=2, dest_idx=4, seat_type="ngoi_mem"),
    ]
    plan = opt.assign_seats(bookings)
    used = [s for s in plan["ngoi_mem"] if not s.get("locked")]

    assert len(used) == 1
    assert len(used[0]["book"]) == 2


def test_assign_seats_overlapping_bookings_need_two_seats():
    bookings = [
        dict(origin_idx=0, dest_idx=3, seat_type="ngoi_mem"),
        dict(origin_idx=1, dest_idx=4, seat_type="ngoi_mem"),
    ]
    plan = opt.assign_seats(bookings)
    used = [s for s in plan["ngoi_mem"] if not s.get("locked")]

    assert len(used) == 2


def test_assign_seats_separates_by_seat_type():
    bookings = [
        dict(origin_idx=0, dest_idx=2, seat_type="ngoi_mem"),
        dict(origin_idx=0, dest_idx=2, seat_type="giuong_nam_k6"),
    ]
    plan = opt.assign_seats(bookings)

    assert len([s for s in plan["ngoi_mem"] if not s.get("locked")]) == 1
    assert len([s for s in plan["giuong_nam_k6"] if not s.get("locked")]) == 1


def test_assign_seats_locked_seats_are_reserved_and_unused():
    bookings = [dict(origin_idx=0, dest_idx=2, seat_type="ngoi_mem")]
    plan = opt.assign_seats(bookings, locked_seat_count={"ngoi_mem": 3})

    locked = [s for s in plan["ngoi_mem"] if s.get("locked")]
    used = [s for s in plan["ngoi_mem"] if not s.get("locked")]

    assert len(locked) == 3
    assert all(s["book"] == [] for s in locked)  # ghế khóa không nhận booking mới
    assert len(used) == 1
    assert len(used[0]["book"]) == 1


def test_assign_seats_locked_seats_do_not_reduce_seats_needed_for_overflow():
    # 2 booking chồng lấn nhưng có 1 ghế bị khóa -> vẫn cần 2 ghế THƯỜNG, ghế khóa
    # không được dùng để giải phóng chồng lấn.
    bookings = [
        dict(origin_idx=0, dest_idx=3, seat_type="ngoi_mem"),
        dict(origin_idx=1, dest_idx=4, seat_type="ngoi_mem"),
    ]
    plan = opt.assign_seats(bookings, locked_seat_count={"ngoi_mem": 1})
    used = [s for s in plan["ngoi_mem"] if not s.get("locked")]

    assert len(used) == 2


def test_seat_count_used_equals_max_overlap_random_bookings():
    random.seed(0)
    nseg = 19
    bookings = []
    for _ in range(40):
        o = random.randint(0, nseg - 1)
        d = min(o + random.randint(1, 4), nseg)
        bookings.append(dict(origin_idx=o, dest_idx=d, seat_type="ngoi_mem"))

    plan = opt.assign_seats(bookings)
    used = [s for s in plan["ngoi_mem"] if not s.get("locked")]

    assert len(used) == opt.max_overlap(bookings, "ngoi_mem", nseg)


# ============================================================
# Lớp B — Ghép đoạn trống (best-fit)
# ============================================================


def test_extract_free_intervals_finds_gap_between_bookings():
    seat = dict(book=[dict(origin_idx=0, dest_idx=5), dict(origin_idx=8, dest_idx=9)])
    free = opt._extract_free_intervals(seat, nstations=10)
    assert free == [(5, 8)]


def test_best_fit_picks_longest_candidate_within_gap():
    candidates = [
        dict(od_id=1, origin_idx=5, dest_idx=6),  # ngắn
        dict(od_id=2, origin_idx=5, dest_idx=8),  # dài nhất, vừa khít
        dict(od_id=3, origin_idx=6, dest_idx=7),  # ngắn hơn
        dict(od_id=4, origin_idx=4, dest_idx=8),  # vượt ra ngoài gap -> không hợp lệ
    ]
    best = opt._best_fit((5, 8), candidates)
    assert best["od_id"] == 2


def test_best_fit_returns_none_when_no_candidate_fits():
    candidates = [dict(od_id=1, origin_idx=0, dest_idx=3)]
    assert opt._best_fit((5, 8), candidates) is None


def test_gap_combination_example_hn_vinh_and_hue_danang():
    """Ví dụ acceptance criteria FR2.5 trong PRD (docs/prd_duong_sat.md mục 7.2):
    "ghế bán HN–Vinh và Huế–ĐN thì đề xuất bán Vinh–Huế". Mã vị trí ga theo thứ tự
    trong ai_service/config.py: HN=0, PLY=1, NDI=2, NBI=3, THO=4, VIN=5, DHO=6, DHA=7,
    HUE=8, DNA=9."""
    hn_vinh = dict(origin_idx=0, dest_idx=5, seat_type="ngoi_mem")
    hue_dna = dict(origin_idx=8, dest_idx=9, seat_type="ngoi_mem")
    seat_plan = opt.assign_seats([hn_vinh, hue_dna])

    vinh_hue_od = dict(od_id=99, origin_idx=5, dest_idx=8, seat_type="ngoi_mem")
    gaps = opt.find_gap_combinations(seat_plan, [vinh_hue_od], nstations=10)

    assert len(gaps) == 1
    gap = gaps[0]
    assert (gap["from_idx"], gap["to_idx"]) == (5, 8)
    assert gap["suggest_od_id"] == 99
    assert gap["suggest_span"] == (5, 8)


def test_gap_combination_skips_locked_seats():
    bookings = [dict(origin_idx=0, dest_idx=2, seat_type="ngoi_mem")]
    seat_plan = opt.assign_seats(bookings, locked_seat_count={"ngoi_mem": 1})

    candidate = dict(od_id=1, origin_idx=2, dest_idx=9, seat_type="ngoi_mem")
    gaps = opt.find_gap_combinations(seat_plan, [candidate], nstations=10)

    # ghế khóa có free_from=+inf nên _extract_free_intervals của nó không sinh khoảng
    # trống nào cắt với vùng còn bán được -> chỉ ghế thường (đã có booking) mới có gap.
    assert all(g["seat_index"] != next(i for i, s in enumerate(seat_plan["ngoi_mem"]) if s.get("locked")) for g in gaps)


def test_gap_combination_no_suggestion_when_no_candidate_fits():
    bookings = [
        dict(origin_idx=0, dest_idx=2, seat_type="ngoi_mem"),
        dict(origin_idx=8, dest_idx=9, seat_type="ngoi_mem"),
    ]
    seat_plan = opt.assign_seats(bookings)
    # candidate quá dài, không nằm gọn trong khoảng trống (2,8)
    too_long = dict(od_id=1, origin_idx=1, dest_idx=8, seat_type="ngoi_mem")

    gaps = opt.find_gap_combinations(seat_plan, [too_long], nstations=10)
    assert gaps == []
