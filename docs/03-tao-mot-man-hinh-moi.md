# 3. Tạo một màn hình mới

## 3.1. Giao diện được ghép từ những mảnh nào

Một trang trong dự án không phải một file khổng lồ, mà là nhiều mảnh ghép lại:

```
┌─────────────────────────────────────────────────────────┐
│  Header.jsx        (thanh trên cùng: tìm kiếm, chuông)   │
├───────────┬─────────────────────────────┬───────────────┤
│           │                             │               │
│ LeftAside │      TRANG CỦA BẠN          │  RightAside   │
│  .jsx     │      (ví dụ MatchLayout)    │    .jsx       │
│           │                             │               │
│  (menu)   │  ┌───────────────────────┐  │  (danh sách   │
│           │  │ MatchScore.jsx        │  │   đang theo   │
│           │  │ (mảnh dùng lại)       │  │   dõi)        │
│           │  └───────────────────────┘  │               │
│           │  ┌───────────────────────┐  │               │
│           │  │ Pagination.jsx        │  │               │
│           │  └───────────────────────┘  │               │
└───────────┴─────────────────────────────┴───────────────┘
```

> 💡 **Component là gì?** Là một mảnh giao diện có thể tái sử dụng, giống viên
> LEGO. Ví dụ `Pagination.jsx` là thanh phân trang — viết một lần, dùng ở 6
> trang khác nhau. Sửa một chỗ là cả 6 trang cùng đổi.

Ba loại thư mục cần phân biệt:

| Thư mục | Chứa gì | Ví dụ |
|---|---|---|
| `client/src/layouts/` | **Trang** — mỗi trang ứng với một đường dẫn | `layouts/home/Match/MatchLayout.jsx` ứng với `/match` |
| `client/src/components/` | **Mảnh dùng lại nhiều nơi** | `components/ui/Pagination.jsx` |
| `layouts/<Trang>/components/` | **Mảnh chỉ trang đó dùng** | `layouts/home/Match/components/MatchScore.jsx` |

Quy tắc chọn chỗ đặt: mảnh chỉ một trang dùng thì để cạnh trang đó; khi trang
thứ hai cần đến thì mới chuyển ra `components/`.

## 3.2. Mổ xẻ trang `/match` (Công ty phù hợp)

File: `client/src/layouts/home/Match/MatchLayout.jsx`

### Phần 1 — Khai báo lấy dữ liệu từ đâu

```jsx
import { useGetMatchedCompaniesQuery } from '../../../services/redux/query/api/matchApi';

const { data, isLoading, isError, error } = useGetMatchedCompaniesQuery(query);
```

Chỉ một dòng, nhưng nó lo hộ bạn rất nhiều việc:

| Biến | Ý nghĩa |
|---|---|
| `isLoading` | Đang chờ máy chủ trả lời |
| `isError` + `error` | Gọi hỏng, kèm thông báo lỗi từ máy chủ |
| `data` | Dữ liệu đã về |

Ngoài ra nó còn **tự nhớ kết quả**: rời trang rồi quay lại trong thời gian ngắn
thì hiện ngay, không gọi máy chủ lần nữa.

> 💡 **RTK Query là gì?** Là thư viện lo toàn bộ việc "gọi API và nhớ kết quả".
> Không có nó, mỗi trang phải tự viết: bật cờ đang tải → gọi → bắt lỗi → lưu
> vào state → tự xoá khi cũ. Đó là khoảng 30 dòng lặp lại ở mọi trang.

### Phần 2 — Ba trạng thái phải xử lý đủ

Đây là chỗ hay bị bỏ sót nhất. Một trang tử tế phải trả lời được cả ba câu:

```jsx
// (a) ĐANG TẢI — nếu không có, người dùng nhìn màn hình trắng và tưởng web hỏng
if (isLoading) return <Loading />;

// (b) LỖI — và lỗi phải nói được người dùng nên làm gì tiếp
if (isError) {
  return (
    <Page>
      <p>{error?.data?.message || 'Không tải được gợi ý.'}</p>
      <Link to='/resume'>Tạo CV ngay</Link>
    </Page>
  );
}

// (c) KHÔNG CÓ DỮ LIỆU — khác với lỗi!
{data?.matches?.length === 0 && <NotFoundItem />}
```

Chú ý cách xử lý lỗi ở trên: khi người dùng **chưa có CV**, máy chủ trả về lỗi
kèm lời nhắc, và giao diện gắn luôn nút *"Tạo CV ngay"*. Báo lỗi mà không chỉ
lối thoát thì người dùng bị kẹt.

### Phần 3 — Nói thật về giới hạn của hệ thống

```jsx
{!data?.semanticAvailable && (
  <p>Đang xếp hạng bằng luật (tiếng Nhật, kinh nghiệm, kỹ năng).
     Phần so khớp theo ngữ nghĩa đang tạm nghỉ.</p>
)}
```

Khi dịch vụ embedder tắt, hệ thống vẫn chấm điểm được nhưng kém tinh hơn. Giao
diện **nói ra điều đó** thay vì im lặng giả vờ mọi thứ vẫn đầy đủ.

### Phần 4 — Bộ lọc gắn vào địa chỉ URL

```jsx
const [searchParams, setSearchParams] = useSearchParams();
const qualifiedOnly = searchParams.get('qualifiedOnly') === 'true';
```

Trạng thái bộ lọc được lưu **trong địa chỉ** (`/match?page=2&qualifiedOnly=true`)
chứ không giấu trong bộ nhớ. Nhờ vậy: bấm F5 không mất bộ lọc, và copy link gửi
cho người khác thì họ thấy đúng thứ bạn đang thấy.

## 3.3. Công thức tạo trang mới

Ví dụ: thêm trang **"Việc làm theo tỉnh"** ở đường dẫn `/jobs-by-prefecture`,
dùng API đã tạo ở [tài liệu 2](02-tao-mot-api-moi.md).

### Bước 1 — Khai báo cách gọi API

Mở `client/src/services/redux/query/api/jobsApi.js`, thêm vào trong
`endpoints`:

```js
    getJobsByPrefecture: builder.query({
      query: () => 'jobs/by_prefecture',
      providesTags: ['jobs'],
    }),
```

Và thêm tên hook vào danh sách xuất ở cuối file:

```js
export const {
  useGetJobsQuery,
  useGetJobsByPrefectureQuery,   // ← thêm dòng này
  ...
} = jobsApi;
```

> 💡 **Quy tắc đặt tên hook:** `getJobsByPrefecture` → `useGetJobsByPrefectureQuery`.
> Thêm `use` ở đầu, `Query` (khi đọc dữ liệu) hoặc `Mutation` (khi thay đổi dữ
> liệu) ở cuối. RTK Query tự sinh ra hook, bạn chỉ cần khai báo đúng tên.

**Chọn file nào?** Mỗi domain một file, đặt trong
`client/src/services/redux/query/api/`:

| File | Phụ trách |
|---|---|
| `usersApi.js` | tài khoản, hồ sơ, theo dõi |
| `postsApi.js` | bài viết, thích, bình luận, lưu bài |
| `channelsApi.js` | channel và lối tắt |
| `jobsApi.js` | việc làm, doanh nghiệp |
| `matchApi.js` | gợi ý công ty, phân tích thiếu sót |
| `resumeApi.js` | CV |
| `chatApi.js` | tin nhắn |
| `notificationsApi.js` | thông báo |

### Bước 2 — Viết trang

Tạo file `client/src/layouts/home/Jobs/JobsByPrefectureLayout.jsx`:

```jsx
import Page from '../../Page';
import Loading from '../../../components/ui/Loading';
import NotFoundItem from '../../../components/ui/NotFoundItem';
import { useTranslation } from 'react-i18next';
import { useGetJobsByPrefectureQuery } from '../../../services/redux/query/api/jobsApi';

function JobsByPrefectureLayout() {
  const { t } = useTranslation('job');
  const { data, isLoading, isError, error } = useGetJobsByPrefectureQuery();

  if (isLoading) return <Loading />;
  if (isError) {
    return (
      <Page>
        <p className='font-bold'>{error?.data?.message || t('loadFailed')}</p>
      </Page>
    );
  }

  return (
    <Page>
      <h1 className='text-2xl font-bold mb-4'>{t('byPrefecture.title')}</h1>
      {data?.prefectures?.length === 0 && <NotFoundItem message={t('empty')} />}
      <ul className='flex flex-col gap-2'>
        {data?.prefectures?.map((p) => (
          <li key={p.name} className='flex justify-between p-3 rounded border
                                      border-neutral-300 dark:border-neutral-700'>
            <span>{p.name}</span>
            <span className='font-bold'>
              {t('byPrefecture.count', { count: p.total })}
            </span>
          </li>
        ))}
      </ul>
    </Page>
  );
}

export default JobsByPrefectureLayout;
```

Bốn điều bắt buộc:

- **Không viết chữ thẳng vào JSX.** Mọi câu chữ đi qua `t('khoá')`, và khoá phải
  có trong **cả ba** file `client/src/i18n/locales/{ja,vi,en}/job.json`. Viết
  `<h1>Việc làm theo tỉnh</h1>` thì ESLint báo lỗi và CI đỏ. Cách thêm khoá mới
  nằm ở [tài liệu 9](09-da-ngon-ngu.md).
- **Bọc trong `<Page>`** để có bố cục chung (menu trái, cột phải).
- **`key={...}` khi dùng `.map()`** — React cần một giá trị duy nhất cho mỗi
  phần tử để biết cái nào vừa đổi. Thiếu nó, danh sách sẽ nhảy lung tung khi
  cập nhật.
- **Dùng `?.` khi đọc dữ liệu từ máy chủ** (`data?.prefectures`) vì lúc trang
  vừa mở, dữ liệu chưa về, `data` còn là `undefined`.

> ⚠️ **Cái bẫy `?.` mà dự án từng dính:** viết `p?.images[0]` là **sai**. Dấu
> `?.` chỉ bảo vệ cho `p`, còn `images` vẫn bị lấy `[0]` thẳng thừng — trống là
> nổ lỗi. Đúng phải là `p?.images?.url`. Lỗi này từng làm **sập cả trang tìm
> kiếm** vì 358/374 bài viết trong kho không có ảnh.

### Bước 3 — Gắn vào bảng đường dẫn

Mở `client/src/services/router/router.jsx`:

```jsx
// 1. Khai báo ở đầu file (lazy = chỉ tải khi người dùng thật sự mở trang)
const JobsByPrefectureLayout = lazy(() =>
  import('../../layouts/home/Jobs/JobsByPrefectureLayout')
);

// 2. Thêm vào mảng children
{
  path: 'jobs-by-prefecture',
  element: (
    <ProtectedRoute>
      <JobsByPrefectureLayout />
    </ProtectedRoute>
  ),
},
```

`<ProtectedRoute>` là chốt chặn: chưa đăng nhập thì tự đá về `/login`.

> 💡 **`lazy` để làm gì?** Không có nó, trình duyệt phải tải code của **tất cả**
> 18 trang ngay từ lần mở đầu tiên. Có `lazy`, code của trang nào chỉ được tải
> khi người dùng bấm vào trang đó, nên lần vào web đầu tiên nhanh hơn nhiều.

### Bước 4 — Thêm vào menu

Mở `client/src/layouts/components/LeftAside.jsx`, thêm một nút theo đúng khuôn
các nút có sẵn:

```jsx
<button
  className='p-2 w-full h-[56px] flex items-center gap-4
             hover:bg-neutral-100 dark:hover:bg-neutral-600 rounded'
  onClick={() => handleRedirect('/jobs-by-prefecture')}
>
  <span dangerouslySetInnerHTML={{ __html: icons.recruitment_icon }}></span>
  <p>{t('jobsByPrefecture')}</p>
</button>
```

`LeftAside.jsx` đã có sẵn `const { t } = useTranslation('nav')` ở đầu file, nên
chỉ cần thêm khoá `jobsByPrefecture` vào ba file `locales/*/nav.json`.

### Bước 5 — Chạy thử

```bash
docker compose up -d --build client
```

⚠️ **Bắt buộc có `--build`.** Mã nguồn giao diện được đóng gói sẵn vào
container, nên sửa file trên máy mà không build lại thì trang vẫn hiện bản cũ.
Đây là chỗ rất hay làm người mới mất thời gian.

Sau đó kiểm tra chất lượng code — CI cũng chạy đúng hai lệnh này:

```bash
cd client
npm run lint     # bắt lỗi cú pháp, biến thừa, biến chưa khai báo
npm run build    # thử đóng gói bản chính thức
```

## 3.4. Khi trang cần thay đổi dữ liệu (không chỉ đọc)

Ví dụ có nút **Lưu**. Dùng `Mutation` thay vì `Query`:

```jsx
import useMutationToast from '../../../hooks/useMutationToast';
import { usePostResumeMutation } from '../../../services/redux/query/api/resumeApi';

const [saveResume, saveResult] = usePostResumeMutation();

// Một dòng này lo hết: hiện thông báo xanh khi thành công, đỏ khi thất bại,
// và ghi lỗi về máy chủ để sau này còn tra được.
useMutationToast(saveResult, {
  onSuccess: () => setForm(formTrong),   // tuỳ chọn: làm gì thêm khi thành công
});

<button onClick={() => saveResume(duLieu)} disabled={saveResult.isLoading}>
  Lưu
</button>
```

`disabled={saveResult.isLoading}` chống bấm hai lần liên tiếp — thiếu nó là
người dùng bấm nhanh tay sẽ tạo ra hai bản ghi trùng.

> 💡 **Trước đây chỗ này lặp 57 lần.** Mỗi trang tự viết ~15 dòng theo dõi
> trạng thái để hiện thông báo. Gom lại thành `useMutationToast` đã xoá 408
> dòng và sửa luôn một lỗi: có trang theo dõi nhầm trạng thái của API khác nên
> thông báo hiện sai thời điểm.

## 3.5. Các mảnh ghép có sẵn — dùng lại, đừng viết lại

| Component | Dùng khi |
|---|---|
| `components/ui/Loading.jsx` | Đang chờ dữ liệu |
| `components/ui/NotFoundItem.jsx` | Danh sách rỗng |
| `components/ui/Pagination.jsx` | Chia trang |
| `components/ui/Table.jsx` | Bảng dữ liệu (trang quản trị) |
| `components/ui/SinglePost.jsx` | Hiển thị một bài viết |
| `layouts/Page.jsx` | Bố cục chung 3 cột |
| `hooks/useMutationToast.jsx` | Thông báo sau khi lưu/xoá |
| `hooks/useDebounce.jsx` | Ô tìm kiếm — chờ người dùng gõ xong mới gọi API |
| `hooks/useObserver.jsx` | Cuộn tới đâu tải tiếp tới đó |
| `hooks/useClickOutside.jsx` | Bấm ra ngoài để đóng modal |

## 3.6. Những lỗi hay gặp

| Hiện tượng | Nguyên nhân |
|---|---|
| Sửa code mà trang không đổi | Quên `docker compose up -d --build client` |
| Trang trắng hoàn toàn | Lỗi lúc vẽ giao diện. Giờ đã có màn hình *"Trang gặp sự cố"* và lỗi được ghi về máy chủ — xem tài liệu 8 |
| `Cannot read properties of undefined` | Đọc dữ liệu khi nó chưa về. Dùng `?.` ở **mọi** mắt xích: `a?.b?.c` |
| Danh sách nhảy loạn khi cập nhật | Thiếu `key` trong `.map()` |
| Bộ lọc mất khi bấm F5 | Trạng thái để trong bộ nhớ thay vì trong URL |
| `npm run lint` báo đỏ | Đọc thông báo, nó chỉ đúng dòng. Đừng bỏ qua — chính lint đã chỉ ra 2 lỗi làm sập trang trong dự án này |
| Màn hình hiện `job.byPrefecture.title` thay vì chữ | Khoá chưa có trong file dịch — xem [tài liệu 9](09-da-ngon-ngu.md) |
| Một dòng ra tiếng Nhật giữa giao diện tiếng Việt | Thiếu khoá ở `locales/vi/` nên rơi về ngôn ngữ mặc định |

---

Tiếp theo: [4. Luồng đăng nhập](04-luong-dang-nhap.md)

Liên quan: [9. Đa ngôn ngữ](09-da-ngon-ngu.md) — nơi cất toàn bộ chữ nghĩa của giao diện
