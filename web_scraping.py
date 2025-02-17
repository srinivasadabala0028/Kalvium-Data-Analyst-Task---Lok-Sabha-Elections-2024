import scrapy
import pandas as pd

class ResultsSpider(scrapy.Spider):
    name = "results"
    start_urls = ['https://results.eci.gov.in/']
    accessed_states_count = 0

    def parse(self, response):
        # Extract parliamentary constituencies and total seats
        parliamentary_constituencies = response.css('.state-item.blue-bg h2::text').get().strip()
        total_seats = response.css('.state-item.blue-bg h1::text').get().strip()

        data = {
            'parliamentary_constituencies': [parliamentary_constituencies],
            'total_seats': [total_seats]
        }

        # Save the basic data to an Excel file
        df_basic = pd.DataFrame(data)
        df_basic.to_excel('results_basic.xlsx', index=False)
        self.log('Saved basic results to results_basic.xlsx')


        yield response.follow('https://results.eci.gov.in/PcResultGenJune2024/index.htm', callback=self.parse_party_results)

    def parse_party_results(self, response):

        party_results = []


        table_rows = response.xpath('//table[@class="table"]/tbody/tr')

        for row in table_rows:
            party_name = row.xpath('td[1]/text()').get().strip() if row.xpath('td[1]/text()').get() else ''
            seats_won_link = row.xpath('td[2]/a/@href').get().strip() if row.xpath('td[2]/a/@href').get() else ''


            if seats_won_link:
                full_link = response.urljoin(seats_won_link)
                yield response.follow(full_link, callback=self.parse_party_won_results, meta={'party_name': party_name})

                # Access each state's website and increment accessed_states_count
                state_dropdown_options = response.css('#ctl00_ContentPlaceHolder1_Result1_ddlState option[value]:not([value=""])')
                for option in state_dropdown_options:
                    state_value = option.css('::attr(value)').get()
                    if state_value:
                        state_url = f'https://results.eci.gov.in/PcResultGenJune2024/{state_value.lower()}.htm'
                        yield scrapy.Request(state_url, callback=self.parse_state_page)
                        self.accessed_states_count += 1

    def parse_party_won_results(self, response):
        party_name = response.meta['party_name']
        won_results = []

        # Extracting all rows from the table
        table_rows = response.xpath('//table[@class="table table-striped table-bordered"]/tbody/tr')

        for row in table_rows:
            s_no = row.xpath('td[1]/text()').get().strip() if row.xpath('td[1]/text()').get() else ''
            constituency_name = row.xpath('td[2]/a/text()').get().strip() if row.xpath('td[2]/a/text()').get() else ''
            winning_candidate = row.xpath('td[3]/text()').get().strip() if row.xpath('td[3]/text()').get() else ''
            total_votes = row.xpath('td[4]/text()').get().strip() if row.xpath('td[4]/text()').get() else ''
            margin = row.xpath('td[5]/text()').get().strip() if row.xpath('td[5]/text()').get() else ''

            won_results.append({
                'Party': party_name,
                'S.No': s_no,
                'Parliament Constituency': constituency_name,
                'Winning Candidate': winning_candidate,
                'Total Votes': total_votes,
                'Margin': margin
            })

        # Save Won Results to an Excel file
        df_won_results = pd.DataFrame(won_results)
        df_won_results.to_excel(f'won_results_{party_name}.xlsx', index=False)
        self.log(f'Saved won results for {party_name} to won_results_{party_name}.xlsx')

    def parse_state_page(self, response):
        state_name = response.css('#state-name::text').get()
        print(f"Accessed {state_name} page")


    def closed(self, reason):
        self.log(f"Successfully accessed {self.accessed_states_count} state pages.")
        print(f"Successfully accessed {self.accessed_states_count} state pages.")


