import datetime

import scrapy

class ConsumoSpider(scrapy.Spider):
    name = 'celesc_consumo'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.start_urls = ['https://agenciaweb.celesc.com.br/AgenciaWeb/autenticar/autenticar.do']

    def parse(self, response, **kwargs):
        return scrapy.FormRequest.from_response(
            response,
            formname="LoginForm",
            formdata={
                "param_url": "/agencia/",
                "sqUnidadeConsumidora": f"{self.uc}",
                "numeroMedidor": "false",
                "tpDocumento": "CPF",
                "numeroDocumentoCPF": f"{self.cpf}",
                "numeroDocumentoCNPJ": "",
                "autenticarSemDocumento": "false",
                "tipoUsuario": "clienteUnCons",
                "senha": f"{self.senha}"
            },
            callback=self.after_login_1
        )

    def after_login_1(self, response, **kwargs):
        return scrapy.FormRequest.from_response(
            response,
            formname="SenhaForm",
            formdata={
                "senha": f"{self.senha}"
            },
            callback=self.after_login_2
        )

    def after_login_2(self, response):
        now = datetime.datetime.now()
        yr_ago = now - datetime.timedelta(days=395)
        return [scrapy.FormRequest(
            url="https://agenciaweb.celesc.com.br/AgenciaWeb/consultarHistoricoConsumo/histCons.do",
            formdata={"mesInicial": f"{yr_ago.month}",
                      "anoInicial": f"{yr_ago.year}",
                      "mesFinal": f"{now.month}",
                      "anoFinal": f"{now.year}"},
            callback=self.parse_data
        )]

    def parse_data(self, response):
        # get data table
        rows = response.css(".fundoLinha1Tabela") + response.css(".fundoLinha2Tabela")
        data = [[" ".join(col.extract().split()) for col in row.xpath('td//text()')] for row in rows]
        # sort to mm/yyyy
        data = sorted(data, key=lambda row: datetime.datetime.strptime(row[0], '%m/%Y'))[::-1]
        # import pdb; pdb.set_trace()
        csv_data = ""
        with open(f"{self.file_out}", "w+") as fp:
            for row in data:
                csv_data += f'"{row[0]}","{row[-1].split()[0]}"\n'
            fp.write(csv_data)
