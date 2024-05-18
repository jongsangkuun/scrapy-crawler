import scrapy
from scrapy_splash import SplashRequest
from test.tutorial.items import TutorialItem

class VipshopSpider(scrapy.Spider):
    name = "vipshop"  # 스파이더에 대한 고유한 이름을 지정합니다.

    def start_requests(self):
        start_urls = "https://list.vip.com/autolist.html?rule_id=53986307&title=%E8%BF%9E%E8%A1%A3%E8%A3%99&refer_url=https%3A%2F%2Fcategory.vip.com%2Fhome"

        # SplashRequest를 사용해 JS 지원 페이지를 처리합니다.
        # 스크립트에서 페이지 아래로 스크롤하는 함수가 포함되어 있습니다.
        yield SplashRequest(
            start_urls,
            callback=self.parse_result,  # 이 페이지를 파싱하는 콜백 함수를 지정합니다.
            endpoint="execute",
            meta={"download_timeout": 600},
            args={
                # 아래 Lua 스크립트는 페이지 끝까지 스크롤하고, 모든 이미지를 로딩한 후 HTML을 반환합니다.
                "lua_source": """
                       -- Add a function to scroll down to the bottom of the page
                       function go_to_bottom(splash)
                           local scroll_to = splash:jsfunc("window.scrollTo")
                           local get_body_height = splash:jsfunc(
                               "function() {return document.body.scrollHeight;}"
                           )
                           for _ = 1, 10 do  -- Adjust the scrolling times to meet your requirement
                               -- Scroll down and wait a little
                               scroll_to(0, get_body_height())
                               splash:wait(1)  -- Adjust the waiting time to meet your requirement
                           end
                       end

                       function main(splash, args)
                           splash.images_enabled = true
                           assert(splash:go(args.url))
                           go_to_bottom(splash)  -- Call the scroll down function here
                           return splash:html()
                       end""",
                "url": start_urls,
                "wait": 10.0,  # 스크립트 실행 후 추가적으로 대기하는 시간을 설정합니다.
            },
        )

    def parse_result(self, response):
        # 상품 목록에 대한 각각의 선택자를 반복합니다.
        for sel in response.css(".goods-list.c-goods-list--normal"):
            item = CnCrawlerItem()

            # 각 상품에 대한 제품명, 가격, URL, 이미지 URL을 추출합니다.
            product_names = sel.css(".c-goods-item__name::text").getall()

            product_prices = sel.css(
                ".c-goods-item__sale-price.J-goods-item__sale-price::text"
            ).getall()

            product_urls = sel.css(
                ".c-goods-item.J-goods-item.c-goods-item--auto-width a::attr(href)"
            ).getall()

            product_image_urls = sel.css("img.J-goods-item__img::attr(src)").getall()

            # 각 상품에 대해 아이템을 생성하고 이를 반환합니다.
            for product_name, product_price, product_url, product_image_url in zip(
                product_names, product_prices, product_urls, product_image_urls
            ):
                item["product_name"] = product_name
                item["product_price"] = product_price + "¥"
                item["product_image_url"] = "https:" + product_image_url
                item["product_url"] = "https:" + product_url

                # item 데이터를 리스트 형테로 만들어 반환합니다.
                yield item
