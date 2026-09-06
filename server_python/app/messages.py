"""Danh mục mã thông báo trả về cho client.

Vì sao cần mã chứ không chỉ câu chữ
-----------------------------------
Giao diện có ba ngôn ngữ (Nhật, Việt, Anh) nhưng phần lớn toast lại lấy chữ
thẳng từ `message` của server (`useMutationToast` bên client). Dịch xong 100%
frontend mà backend vẫn trả tiếng Việt thì toast vẫn ra tiếng Việt.

Cách xử lý: mỗi thông báo có một **mã ổn định** (`auth.emailExists`). Response
mang cả mã lẫn câu tiếng Việt::

    {"error": true, "success": false,
     "message": "Địa chỉ email đã tồn tại!",
     "code": "auth.emailExists"}

Client dịch theo `code`; không có bản dịch thì rơi về `message`. Nhờ vậy:

* Thêm một endpoint mới quên đặt mã -> người dùng vẫn thấy câu tiếng Việt,
  không thấy khoá thô.
* Backend KHÔNG phải biết người dùng đang xem ngôn ngữ nào — không đọc
  `Accept-Language`, không giữ ba bản dịch trong Python. Bản dịch chỉ nằm một
  chỗ duy nhất: `client/src/i18n/locales/*/error.json`.

Chỗ đặt tham số
---------------
Thông báo có phần thay đổi được viết theo kiểu `str.format`::

    "upload.tooLarge": "File vượt quá {max}MB."

và `params` đi kèm trong response để client tự ghép vào bản dịch của mình.
Không bao giờ nhét sẵn giá trị vào câu rồi gửi chuỗi đã ghép — làm thế client
hết đường dịch.
"""

MESSAGES: dict[str, str] = {
    # --- chung -------------------------------------------------------------
    "server.generic": "Đã có lỗi xảy ra, vui lòng thử lại sau!",
    "common.invalidId": "Định danh không hợp lệ!",
    "common.invalidValue": "Giá trị '{field}' không hợp lệ!",
    "common.invalidPayload": "Dữ liệu gửi lên không hợp lệ!",
    "common.invalidPayloadFields": "Dữ liệu gửi lên không hợp lệ ở: {fields}",
    "common.tooManyRequests": "Bạn thao tác quá nhiều lần, vui lòng thử lại sau ít phút!",
    # --- xác thực & phân quyền --------------------------------------------
    "auth.missingToken": "Token không tồn tại",
    "auth.invalidOrExpiredToken": "Token đã hết hạn hoặc không hợp lệ.",
    "auth.invalidToken": "Token không chính xác!",
    "auth.adminOnly": "Chức năng này chỉ dành cho admin!",
    "auth.notEnoughPermission": "Bạn không đủ quyền!",
    "auth.credentialsRequired": "Yêu cầu cần có email và password!",
    "auth.emailExists": "Địa chỉ email đã tồn tại!",
    "auth.invalidCredentials": "Email hoặc mật khẩu không đúng!",
    "auth.sessionExpired": "Phiên đăng nhập đã hết hạn, vui lòng đăng nhập lại!",
    "auth.registered": "Tạo tài khoản thành công!",
    "auth.loggedOut": "Đăng xuất tài khoản thành công!",
    # --- tải file ----------------------------------------------------------
    "upload.unsupportedType": "Định dạng file không được hỗ trợ. Chỉ nhận: {allowed}",
    "upload.tooLarge": "File vượt quá {max}MB.",
    # --- người dùng --------------------------------------------------------
    "user.notFound": "Không tìm thấy người dùng!",
    "user.cannotEditOthers": "Bạn không thể sửa thông tin của người khác!",
    "user.wrongOldPassword": "Mật khẩu cũ không chính xác!",
    "user.updated": "Cập nhật người dùng thành công!",
    # --- theo dõi ----------------------------------------------------------
    "follow.cannotFollowSelf": "Bạn không thể tự follow bản thân!",
    "follow.followed": "Follow tài khoản thành công!",
    "follow.unfollowed": "Hủy follow tài khoản thành công!",
    "follow.followingRemoved": "Hủy theo dõi người dùng thành công!",
    "follow.followerRemoved": "Gỡ thành công người dùng ra khỏi danh sách theo dõi!",
    # --- bài viết ----------------------------------------------------------
    "post.notFound": "Không tìm thấy bài viết!",
    "post.contentAndChannelRequired": "Yêu cầu bài viết phải có nội dung và channelId!",
    "post.invalidOldImages": "Dữ liệu ảnh cũ không hợp lệ!",
    "post.cannotEditOthers": "Bạn không thể sửa bài viết của người khác hoặc bài viết trong channel đã bị xóa!",
    "post.cannotDeleteOthers": "Bạn không thể xóa bài viết của người khác",
    "post.emptyComment": "Không thể đăng bình luận trống!",
    "post.created": "Tạo bài viết thành công!",
    "post.updated": "Cập nhật bài viết thành công",
    "post.deleted": "Xóa bài viết thành công!",
    "post.liked": "Thích bài viết thành công!",
    "post.unliked": "Hủy thích bài viết thành công!",
    "post.saved": "Lưu bài viết thành công!",
    "post.unsaved": "Hủy lưu bài viết thành công!",
    "post.commented": "Đăng bình luận thành công",
    "post.commentDeleted": "Xoá bình luận thành công!",
    # --- channel -----------------------------------------------------------
    "channel.notFound": "Channel không tồn tại!",
    "channel.exists": "Channel đã tồn tại!",
    "channel.notJoined": "Bạn chưa tham gia channel này!",
    "channel.notJoinedShortcut": "Bạn chưa gia nhập channel này!",
    "channel.adminCannotLeave": "Admin không thể tự ý rời khỏi nhóm!",
    "channel.cannotRemoveSelf": "Bạn không thể xóa chính mình ra khỏi channel!",
    "channel.cannotRemoveOtherAdmin": "Bạn không thể xóa admin khác ra khỏi nhóm!",
    "channel.invalidOldBackground": "Dữ liệu ảnh nền cũ không hợp lệ!",
    "channel.created": "Tạo channel thành công!",
    "channel.joined": "Gia nhập channel thành công!",
    "channel.left": "Bạn đã thoát nhóm channel!",
    "channel.updated": "Cập nhật channel thành công!",
    "channel.deleted": "Xóa channel thành công!",
    "channel.userRemoved": "Đã xóa người dùng khỏi channel!",
    # --- hội thoại ---------------------------------------------------------
    "chat.conversationNotFound": "Không tìm thấy hội thoại!",
    # --- việc làm & doanh nghiệp ------------------------------------------
    "job.notFound": "Không tìm thấy tin tuyển dụng!",
    "company.notFound": "Không tìm thấy công ty!",
    "company.noOpenJobs": "Công ty này chưa có vị trí nào đang tuyển!",
    # --- CV & gợi ý --------------------------------------------------------
    "resume.saved": "Lưu CV thành công!",
    "match.noResume": "Bạn cần tạo CV trước khi dùng chức năng gợi ý công ty phù hợp!",
    # --- website & quản trị -----------------------------------------------
    "web.invalidOldLogo": "Dữ liệu logo cũ không hợp lệ!",
    "web.updated": "Cập nhật thông tin website thành công!",
    "admin.unknownSource": "Nguồn không tồn tại: {sources}",
    "admin.pagesOutOfRange": "Số trang phải trong khoảng 1-{max}",
    "admin.detailOutOfRange": "Số tin làm giàu phải trong khoảng 0-{max}",
    "admin.etlRunning": "Đang có một mẻ ETL chạy, vui lòng đợi hoàn tất!",
    "admin.etlStarted": "Đã bắt đầu thu thập dữ liệu, theo dõi ở /api/admin/etl/status",
    # --- log của client ----------------------------------------------------
    "log.received": "Đã ghi nhận!",
}


class UnknownMessageCode(KeyError):
    """Mã không có trong danh mục — lỗi lập trình, không phải lỗi người dùng."""


def message_for(code: str, params: dict | None = None) -> str:
    """Câu tiếng Việt của một mã, đã ghép tham số.

    Ném lỗi khi mã không tồn tại thay vì trả chuỗi rỗng: một mã gõ sai phải
    nổ ngay lúc chạy test, chứ không âm thầm biến thành toast trống.
    """
    try:
        template = MESSAGES[code]
    except KeyError as err:
        raise UnknownMessageCode(code) from err
    return template.format(**params) if params else template
