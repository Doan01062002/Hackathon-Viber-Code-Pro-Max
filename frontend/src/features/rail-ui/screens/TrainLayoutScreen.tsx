import { SectionCard } from "@/features/rail-ui/components/Primitives";
import { selectedCoach, trainCoaches } from "@/features/rail-ui/mockData";

function seatClass(value: string) {
  if (value === "selected") return "seat-selected";
  if (value === "held") return "seat-held";
  if (value === "blocked") return "seat-blocked";
  return "seat-available";
}

export function TrainLayoutScreen() {
  return (
    <div className="page-stack">
      <SectionCard
        title="Danh sách toa tàu"
        subtitle="Chọn toa cần theo dõi hoặc thao tác giữ chỗ, khóa ghế và ưu tiên bán."
      >
        <div className="course-grid">
          {trainCoaches.map((coach) => (
            <article className="course-card course-card-wide" key={coach.name}>
              <div className="course-icon" aria-hidden="true">
                {coach.name.slice(-2)}
              </div>
              <strong>{coach.name}</strong>
              <p>{coach.type}</p>
              <div className="progress-wrap">
                <div className="progress-track">
                  <span className="progress-fill" style={{ width: coach.occupancy }} />
                </div>
                <span>Tải {coach.occupancy}</span>
              </div>
              <button className="btn btn-primary" type="button">
                Chọn toa
              </button>
            </article>
          ))}
        </div>
      </SectionCard>

      <div className="two-up">
        <SectionCard title="Sơ đồ ghế chi tiết" subtitle={`${selectedCoach.route} • ${selectedCoach.coach}`}>
          <div className="seat-map">
            {selectedCoach.seats.map((row, rowIndex) => (
              <div className="seat-row" key={`row-${rowIndex}`}>
                {row.map((seat, seatIndex) => (
                  <button
                    aria-label={`Ghế hàng ${rowIndex + 1} vị trí ${seatIndex + 1}`}
                    className={`seat ${seatClass(seat)}`}
                    key={`seat-${rowIndex}-${seatIndex}`}
                    type="button"
                  >
                    {rowIndex + 1}
                    {seatIndex + 1}
                  </button>
                ))}
              </div>
            ))}
          </div>
        </SectionCard>

        <SectionCard
          title="Chú giải và thao tác"
          subtitle="Phục vụ điều độ hoặc nhân sự vận hành khi cần can thiệp vào từng ghế."
        >
          <div className="stack-list">
            {selectedCoach.seatLegend.map((item) => (
              <div className="legend-row" key={item.label}>
                <span className={`legend-swatch ${seatClass(item.tone)}`} />
                <strong>{item.label}</strong>
              </div>
            ))}
          </div>

          <div className="action-row action-row-vertical">
            <button className="btn btn-primary" type="button">
              Giữ hoặc mở khóa ghế
            </button>
            <button className="btn btn-ghost" type="button">
              Ưu tiên nhóm ghế
            </button>
            <button className="btn btn-ghost" type="button">
              Chuyển sang quota chặng
            </button>
          </div>
        </SectionCard>
      </div>
    </div>
  );
}
