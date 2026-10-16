# Международное SEO ST8 AI: ручные действия

Подготовлено 16 октября 2026. Документ описывает действия владельца сайта после публикации новых файлов. В этой работе не выполняются push, изменение DNS, подача заявок в каталоги или запросы индексации. Цель страниц — обращения по конкретным процессам; позиции и сроки роста не обещаются.

## Карта новых разделов

| Рынок | Посадочная страница | Основная фраза |
|---|---|---|
| UAE, EN | `/ae/ai-facility-management.html` | AI facility management UAE |
| UAE, EN | `/ae/restaurant-automation.html` | AI for restaurants UAE |
| UAE, EN | `/ae/ai-for-hotels-hospitality.html` | AI automation hospitality UAE |
| UAE, EN | `/ae/ai-concierge.html` | AI concierge for restaurants and hotels |
| Türkiye, TR | `/tr/restoran-yapay-zeka-otomasyonu.html` | restoran yapay zeka otomasyonu |
| Türkiye, TR | `/tr/otel-yapay-zeka-cozumleri.html` | otel yapay zeka çözümleri |
| Türkiye, TR | `/tr/tesis-yonetimi-yapay-zeka.html` | tesis yönetimi yapay zeka |

Каталоги статей: `/ae/blog/` и `/tr/blog/`. Новые статьи:

- `/ae/blog/ai-facility-management-one-site-pilot.html`
- `/ae/blog/how-restaurants-dark-kitchens-cut-costs-ai.html`
- `/ae/blog/how-to-run-ai-pilot-one-location.html`
- `/tr/blog/restoranlarda-yapay-zeka-maliyet-dusurme.html`
- `/tr/blog/otel-tesis-yonetimi-yapay-zeka-pilot.html`

## 1. Публикация, sitemap и Search Console

Сначала выполните обычную публикацию и дождитесь успешного GitHub Actions. Затем из репозитория запустите:

```powershell
.\tools\post-deploy-check.ps1 -BaseUrl https://st8-ai.ru
```

При FAIL сначала разберите конкретный URL. Проверьте также новую форму, её сообщение и переход в WhatsApp. Скрипт проверяет HTTP/HTML и наличие кода счётчиков, но не подтверждает доставку заявки или поступление события в кабинет аналитики.

В Search Console откройте подтверждённое свойство `st8-ai.ru` либо соответствующее URL-prefix property `https://st8-ai.ru/`. В разделе Sitemaps отправьте `https://st8-ai.ru/sitemap.xml`, если он ещё не добавлен, и проверьте результат чтения. Sitemap — основной способ сообщить о наборе новых страниц. [Инструкция Google по повторному обходу](https://developers.google.com/search/docs/crawling-indexing/ask-google-to-recrawl).

Для приоритетных семи посадочных по очереди используйте URL Inspection: вставьте полный URL, проверьте доступность опубликованной версии, выполните Test live URL, затем Request indexing. Повторите для пяти статей и двух каталогов по мере доступной квоты. Сохраните дату запроса и состояние URL. Отправка запроса не гарантирует индексацию и не ускоряется многократным повторением для одного адреса. [URL Inspection: официальная справка](https://support.google.com/webmasters/answer/9012289).

После появления данных проверяйте выбранный Google canonical, статус индексации и причины исключения. Сопоставляйте запросы, страны и посадочные страницы. При отсутствии показов сначала проверьте, была ли страница проиндексирована и какой canonical выбран, затем оценивайте содержание и внутренние ссылки.

## 2. Hreflang и границы языковых связок

У каждого нового URL есть собственный canonical. Парные посадочные FM, restaurants и hotels связаны EN-AE ↔ TR; их x-default указывает на английский вариант. Статьи о ресторанных расходах также составляют локализованную пару. Каталоги `/ae/blog/` и `/tr/blog/` связаны между собой.

У concierge и самостоятельных руководств без соответствующего перевода стоят self-reference и x-default на сам материал. Руководство по FM и турецкая статья одновременно об отеле и управлении объектом имеют разный охват, поэтому не объявлены переводами друг друга. Связанные темы соединены обычными ссылками. В sitemap повторены существующие HTML-связки, включая международные главные; расширение использует namespace XHTML. [Правила Google для локализованных версий](https://developers.google.com/search/docs/specialty/international/localized-versions).

При добавлении перевода обновляйте обе страницы и sitemap одновременно. Ссылка hreflang должна вести на реальную эквивалентную страницу, а не на ближайшую по отрасли. Текст FAQ в JSON-LD должен совпадать с видимыми вопросами и ответами. Разметка помогает описать страницу, но не является обещанием особого поискового сниппета.

## 3. Cloudflare CDN при хостинге на reg.ru

Это план ручной настройки. Сам сайт и FTPS-публикация остаются на reg.ru. CDN требует отдельной проверки DNS и HTTPS; фактические настройки текущей учётной записи здесь не изменялись.

Перед переносом авторитетной DNS-зоны экспортируйте действующие записи и сохраните текущие nameserver. Сверьте A/AAAA, www, MX, SPF, DKIM, DMARC, verification TXT и используемые поддомены. Не копируйте предполагаемые IP: адрес origin возьмите из действующей панели хостинга. Автосканирование DNS в Cloudflare нужно сверить с исходной зоной вручную. [Добавление домена](https://developers.cloudflare.com/learning-paths/get-started/add-domain-to-cf/).

Добавьте `st8-ai.ru` в свою учётную запись Cloudflare. Для стандартного full setup получите назначенные Cloudflare nameserver и укажите именно их у регистратора. Не подменяйте их примерами из инструкции. Панель reg.ru различает DNS домена и настройки сайта на хостинге; после смены nameserver источник управления DNS будет Cloudflare. [Cloudflare full setup](https://developers.cloudflare.com/dns/zone-setups/full-setup/setup/) и [привязка домена к хостингу reg.ru](https://help.reg.ru/support/hosting/privyazka-domena-k-hostingu/kak-privyazat-domen-k-hostingu).

Проксируйте только веб-записи для сайта. Почтовые и FTP-хосты оставьте DNS only. MX/TXT сохраняются с действующими значениями. Проверьте, что `FTP_HOST` в Actions указывает на технический origin-хост или IP для FTPS, а не на проксируемое веб-имя; значение секрета в документацию не переносите. [Cloudflare: DNS-only для почты и не-HTTP протоколов](https://developers.cloudflare.com/dns/proxy-status/use-cases/).

До включения Full (strict) проверьте HTTPS origin на reg.ru и действующий сертификат для домена. Затем выберите Full (strict), убедитесь в активности edge-сертификата и проверьте отсутствие циклов редиректа. [Требования к Full (strict)](https://developers.cloudflare.com/ssl/origin-configuration/ssl-modes/full-strict/).

На первом этапе используйте стандартное кеширование статических ресурсов. HTML по умолчанию не кешируется; отдельное правило Cache Rules требует проверки обновлений страниц после FTPS. Для этого статического сайта его можно рассматривать отдельно, когда понятны условия очистки кеша. Не распространяйте правило на внешнюю отправку Web3Forms. После изменения правил очистите затронутые URL, проверьте свежую HTML-версию, robots и sitemap; robots также может кешироваться. [Начало работы с Cache](https://developers.cloudflare.com/cache/get-started/), [поведение по умолчанию](https://developers.cloudflare.com/cache/concepts/default-cache-behavior/).

После настройки повторите пост-деплойный скрипт, откройте AE/TR с мобильного, проверьте форму и WhatsApp. Отдельно проверьте почту и следующий FTPS-деплой. Сравнивайте загрузку до/после при одинаковых условиях; CDN не гарантирует позиции и не меняет национальную принадлежность домена.

## 4. Профили компании: заполнить вручную

Используйте единые название ST8 AI, `info@st8-ai.ru`, существующий телефон, реальные сведения о команде и текущие страницы сайта. До создания ищите уже существующий профиль, чтобы не плодить дубли. Фактическое место работы и рынки обслуживания — разные поля: офис в ОАЭ или Турции не следует указывать без основания. Не заполняйте неизвестные размер команды, дату основания, выручку или финансирование предполагаемыми значениями.

| Площадка | Ручное действие | Какие материалы использовать |
|---|---|---|
| Clutch | Открыть Get listed, войти/зарегистрироваться, выбрать подходящий профиль и заполнить карточку для модерации. | Описание конкретных AI-пилотов, сайт, реальные контакты, существующие кейсы. Отзывы — только от реальных клиентов с их согласия. |
| GoodFirms | Открыть Get Listed, перейти к регистрации и созданию профиля поставщика услуг. | Реальные услуги, отрасли и ссылки; публикуемые утверждения и условия проверить перед отправкой. |
| Crunchbase | После регистрации и требуемой социальной аутентификации найти Create Profile, выбрать организацию, заполнить известные сведения. | Название, сайт, описание, фактическая локация и подтверждённые данные основателей. Пустые неизвестные поля не заменять догадками. |
| Product Hunt | Создать личную учётную запись, пройти onboarding; для конкретного доступного продукта подготовить draft через Post. | Рабочая страница продукта, демонстрация, собственные изображения и точные условия доступа. Сервисный лендинг сам по себе не подменяет запускаемый продукт. |

Официальные инструкции: [Clutch Get listed](https://help.clutch.co/en/knowledge/get-listed-on-clutch), [GoodFirms Get Listed](https://www.goodfirms.co/get-listed), [Crunchbase Create Profile](https://support.crunchbase.com/hc/en-us/articles/115011823988-How-do-I-create-a-Crunchbase-profile), [Product Hunt: posting a product](https://help.producthunt.com/en/articles/479557-how-to-post-a-product). У Product Hunt размещение выполняется личным аккаунтом; готовность конкретного продукта нужно подтвердить перед отправкой. Регистрация и одобрение профиля не являются гарантией трафика или заявок. Платные предложения не подключались.

## 5. Десять EN-запросов для еженедельного наблюдения

Это стартовый список гипотез спроса, без выдуманных частотностей и текущих позиций. Фиксируйте UAE, английский язык, выбранный город и устройство одинаково каждую неделю. В Search Console отдельно фильтруйте страну United Arab Emirates и новые URL; средняя позиция GSC отличается от результата ручного поиска.

| № | Запрос | Целевой URL |
|---|---|---|
| 1 | AI facility management UAE | `/ae/ai-facility-management.html` |
| 2 | facilities management AI automation | `/ae/ai-facility-management.html` |
| 3 | AI for FM companies | `/ae/ai-facility-management.html` |
| 4 | AI for restaurants UAE | `/ae/restaurant-automation.html` |
| 5 | restaurant AI automation UAE | `/ae/restaurant-automation.html` |
| 6 | AI voice host restaurant UAE | `/ae/restaurant-automation.html` |
| 7 | dark kitchen automation UAE | `/ae/restaurant-automation.html` |
| 8 | AI automation hospitality UAE | `/ae/ai-for-hotels-hospitality.html` |
| 9 | AI guest assistant hotel UAE | `/ae/ai-for-hotels-hospitality.html` |
| 10 | AI concierge for restaurants and hotels | `/ae/ai-concierge.html` |

## 6. Десять TR-запросов для еженедельного наблюдения

Фиксируйте Türkiye, турецкий язык, выбранный город и устройство. В GSC отдельно смотрите страну Türkiye/Turkey, язык фактического запроса и посадочную страницу. Не меняйте локацию проверки от недели к неделе и не принимайте отсутствие показов за конкретную отрицательную позицию.

| № | Запрос | Целевой URL |
|---|---|---|
| 1 | restoran yapay zeka otomasyonu | `/tr/restoran-yapay-zeka-otomasyonu.html` |
| 2 | restoran sipariş yapay zeka | `/tr/restoran-yapay-zeka-otomasyonu.html` |
| 3 | restoran için yapay zeka asistanı | `/tr/restoran-yapay-zeka-otomasyonu.html` |
| 4 | otel yapay zeka çözümleri | `/tr/otel-yapay-zeka-cozumleri.html` |
| 5 | otel için yapay zeka | `/tr/otel-yapay-zeka-cozumleri.html` |
| 6 | tesis yönetimi yapay zeka | `/tr/tesis-yonetimi-yapay-zeka.html` |
| 7 | yapay zeka ile tesis yönetimi | `/tr/tesis-yonetimi-yapay-zeka.html` |
| 8 | restoran yapay zeka maliyet düşürme | `/tr/blog/restoranlarda-yapay-zeka-maliyet-dusurme.html` |
| 9 | otel misafir yapay zeka asistanı | `/tr/otel-yapay-zeka-cozumleri.html` |
| 10 | tesis yönetimi yapay zeka pilot uygulama | `/tr/blog/otel-tesis-yonetimi-yapay-zeka-pilot.html` |

Запись недели: дата, страна/город, устройство, запрос, целевой и фактически показанный URL, индексируется ли страница, показы, клики и средняя позиция из GSC. Обращения оценивайте отдельно по посадочной и каналу: `lead_form` для подтверждённой формы, события WhatsApp — как переходы в мессенджер. Клиентские результаты и продажи из этих технических событий автоматически не выводятся.

## 7. Когда рассматривать отдельный международный домен

`.ru` — национальный домен, связанный с Россией. Google использует национальную доменную зону как региональный сигнал; hreflang и CDN не превращают её в нейтральный gTLD. Это ограничение нужно учитывать при оценке международной стратегии, без обещания, что один перенос изменит позиции. [Официальное руководство Google по мультирегиональным сайтам](https://developers.google.com/search/docs/specialty/international/managing-multi-regional-sites?hl=ru).

Отдельный нейтральный международный домен имеет смысл рассматривать, когда международные продажи становятся устойчивым самостоятельным направлением, есть ресурс поддерживать EN/TR-контент, достоверные сведения о работе на этих рынках и план ссылок, аналитики и обработки заявок. Решение опирается на фактические показы, обращения и бизнес-потребность, а не на придуманный порог посещений.

Если решение принято, нужен отдельный план миграции: соответствие старых и новых URL, постоянные редиректы для действительно перенесённых страниц, self-canonical, взаимные hreflang, новые sitemap, подтверждённые свойства Search Console и проверка лидов. Не держите одинаковые международные разделы без выбранного канонического адреса. Домен не покупался, миграция и новые редиректы не выполнялись.

## 8. Турецкие формулировки для редакторской проверки

- В поисковых title/h1 сохранено заданное `yapay zeka`; в основной речи используется также нормативное `yapay zekâ`. Обе записи понятны, но редактору стоит утвердить единый стиль вне точных целевых заголовков.
- Неграмматичный поисковый фрагмент `restoran sipariş yapay zeka` раскрыт как `Sipariş süreçlerinde yapay zekâ...`; буквального набора слов ради вхождения в связный текст нет. Сырой запрос оставлен в таблице отслеживания.
- `Tesis yönetimi` используется для управления зданием/объектом и заявками, а не как обещание полной автоматизации производства. Проверьте соответствие терминологии целевой аудитории FM.
- `Standart reçete kartları` передаёт смысл существующих ТТК Unik Food. Отраслевой редактор может предпочесть `standart reçete` или `üretim reçetesi`; текст не объявляет российский документ турецким нормативным стандартом.
- `Tek noktada pilot` в заданном заголовке, `tek işletmede` для ресторана и `tek tesiste` для отеля описывают один физический объект. Для договора термин объекта нужно определить точнее.
- `KPI’lar`, `ön inceleme` и `personele devir` выбраны для делового текста. В договорной версии можно раскрыть KPI как `temel performans göstergeleri`; юридическая форма договора на турецком здесь не составлялась.
- У новой формы TR ссылка на существующую английскую политику явно помечена `Gizlilik bildirimi (İngilizce)`. Турецкая политика или подтверждение соответствия KVKK не создавались. Их подготовка — отдельная задача владельца.

Турецкий текст вычитан по смыслу и согласованности терминов при подготовке. Независимая проверка человеком — носителем языка в эту работу не входила и не заявляется как выполненная.
