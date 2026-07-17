import { SectionCard } from "@/features/rail-ui/components/Primitives";
import { quoteResult } from "@/features/rail-ui/mockData";

export function QuoteScreen() {
  return (
    <div className="page-stack">
      <SectionCard title="Biểu mẫu báo giá" subtitle="Nhập luồng OD, loại chỗ và ngày đi để xem giá đề xuất.">
        <div className="form-grid">
          <label className="field">
            <span>Ga đi</span>
            <input className="input" defaultValue={quoteResult.origin} />
          </label>
          <label className="field">
            <span>Ga đến</span>
            <input className="input" defaultValue={quoteResult.destination} />
          </label>
          <label className="field">
            <span>Loại chỗ</span>
            <input className="input" defaultValue={quoteResult.seatType} />
          </label>
          <label className="field">
            <span>Ngày đi</span>
            <input className="input" defaultValue="19/07/2026" />
          </label>
        </div>
      </SectionCard>

      <div className="two-up">
        <SectionCard title="Kết quả báo giá" subtitle="Giá cuối cùng, tồn chỗ và chi phí cơ hội.">
          <div className="quote-card">
            <div>
              <span className="mini-label">Giá đề xuất</span>
              <strong className="quote-price">{quoteResult.finalPrice}</strong>
            </div>
            <div className="quote-meta">
              <article>
                <span>Khả dụng</span>
                <strong>{quoteResult.availability}</strong>
              </article>
              <article>
                <span>Chi phí cơ hội</span>
                <strong>{quoteResult.opportunityCost}</strong>
              </article>
              <article>
                <span>Nút cổ chai</span>
                <strong>{quoteResult.bottleneck}</strong>
              </article>
            </div>
          </div>
        </SectionCard>

        <SectionCard
          title="Thẻ diễn giải giá"
          subtitle="Giải thích đủ rõ để bộ phận kinh doanh có thể tự tin ra quyết định."
        >
          <div className="explain-card">
            <p>{quoteResult.explanation}</p>
            <ul className="tag-list">
              <li>Bid price cao</li>
              <li>Nhu cầu vượt tồn kho</li>
              <li>Ưu tiên luồng dài</li>
            </ul>
          </div>
        </SectionCard>
      </div>

      <SectionCard
        title="Lựa chọn thay thế"
        subtitle="Đề xuất các phương án gần nhất để giữ tỷ lệ chuyển đổi khi route chính nóng."
      >
        <div className="stack-list">
          {quoteResult.alternatives.map((item) => (
            <article className="list-card" key={item.label}>
              <div>
                <strong>{item.label}</strong>
                <p>{item.note}</p>
              </div>
              <div className="list-aside">
                <strong>{item.price}</strong>
                <button className="btn btn-ghost" type="button">
                  Chọn phương án
                </button>
              </div>
            </article>
          ))}
        </div>
      </SectionCard>
    </div>
  );
}
