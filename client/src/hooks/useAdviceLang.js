import { useTranslation } from 'react-i18next';

/**
 * Ngôn ngữ gửi kèm khi xin lời khuyên của LLM.
 *
 * Phần `gaps` gửi `code` + `params` để giao diện tự ghép câu, nhưng lời khuyên
 * là văn xuôi nên phải được SINH SẴN đúng ngôn ngữ — backend cần biết đang hỏi
 * bằng tiếng gì. Cắt phần vùng ("en-US" -> "en") vì backend chỉ nhận ja/vi/en.
 */
export default function useAdviceLang() {
  const { i18n } = useTranslation();
  return (i18n.resolvedLanguage || i18n.language || 'ja').split('-')[0];
}
