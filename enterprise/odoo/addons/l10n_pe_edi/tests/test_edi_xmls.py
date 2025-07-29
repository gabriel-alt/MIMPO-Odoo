# -*- coding: utf-8 -*
from odoo import Command
from odoo.tests import tagged
from .common import TestPeEdiCommon, mocked_l10n_pe_edi_post_invoice_web_service
from unittest.mock import patch

from freezegun import freeze_time


@tagged('post_install_l10n', 'post_install', '-at_install')
class TestEdiXmls(TestPeEdiCommon):

    def test_invoice_simple_case(self):
        with freeze_time(self.frozen_today), \
             patch('odoo.addons.l10n_pe_edi.models.account_edi_format.AccountEdiFormat._l10n_pe_edi_post_invoice_web_service',
                   new=mocked_l10n_pe_edi_post_invoice_web_service):
            move = self._create_invoice()
            move.action_post()

            generated_files = self._process_documents_web_services(move, {'pe_ubl_2_1'})
            self.assertTrue(generated_files)
            zip_edi_str = generated_files[0]
            edi_xml = self.edi_format._l10n_pe_edi_unzip_edi_document(zip_edi_str)

            current_etree = self.get_xml_tree_from_string(edi_xml)
            expected_etree = self.get_xml_tree_from_string(self.expected_invoice_xml_values)
            self.assertXmlTreeEqual(current_etree, expected_etree)

    def test_refund_simple_case(self):
        with freeze_time(self.frozen_today), \
             patch('odoo.addons.l10n_pe_edi.models.account_edi_format.AccountEdiFormat._l10n_pe_edi_post_invoice_web_service',
                   new=mocked_l10n_pe_edi_post_invoice_web_service):
            move = self._create_refund()
            (move.reversed_entry_id + move).action_post()

            generated_files = self._process_documents_web_services(move, {'pe_ubl_2_1'})
            self.assertTrue(generated_files)
            zip_edi_str = generated_files[0]
            edi_xml = self.edi_format._l10n_pe_edi_unzip_edi_document(zip_edi_str)

            current_etree = self.get_xml_tree_from_string(edi_xml)
            expected_etree = self.get_xml_tree_from_string(self.expected_refund_xml_values)
            self.assertXmlTreeEqual(current_etree, expected_etree)

    def test_debit_note_simple_case(self):
        with freeze_time(self.frozen_today), \
             patch('odoo.addons.l10n_pe_edi.models.account_edi_format.AccountEdiFormat._l10n_pe_edi_post_invoice_web_service',
                   new=mocked_l10n_pe_edi_post_invoice_web_service):
            move = self._create_debit_note()
            (move.debit_origin_id + move).action_post()

            generated_files = self._process_documents_web_services(move, {'pe_ubl_2_1'})
            self.assertTrue(generated_files)
            zip_edi_str = generated_files[0]
            edi_xml = self.edi_format._l10n_pe_edi_unzip_edi_document(zip_edi_str)

            current_etree = self.get_xml_tree_from_string(edi_xml)
            expected_etree = self.get_xml_tree_from_string(self.expected_debit_note_xml_values)
            self.assertXmlTreeEqual(current_etree, expected_etree)

    def test_invoice_payment_term_detraction_case(self):
        """ Invoice in USD with detractions and multiple payment term lines"""
        self.product.l10n_pe_withhold_percentage = 10
        self.product.l10n_pe_withhold_code = '001'
        with freeze_time(self.frozen_today), \
                patch('odoo.addons.l10n_pe_edi.models.account_edi_format.AccountEdiFormat._l10n_pe_edi_post_invoice_web_service',
                   new=mocked_l10n_pe_edi_post_invoice_web_service):
            update_vals_dict = {"l10n_pe_edi_operation_type": "1001",
                                "invoice_payment_term_id": self.env.ref("account.account_payment_term_advance_60days").id}
            invoice = self._create_invoice(**update_vals_dict).with_context(edi_test_mode=True)
            invoice.action_post()

            generated_files = self._process_documents_web_services(invoice, {'pe_ubl_2_1'})
            self.assertTrue(generated_files)
        zip_edi_str = generated_files[0]
        edi_xml = self.edi_format._l10n_pe_edi_unzip_edi_document(zip_edi_str)
        current_etree = self.get_xml_tree_from_string(edi_xml)
        expected_etree = self.get_xml_tree_from_string(self.expected_invoice_xml_values)
        expected_etree = self.with_applied_xpath(
            expected_etree,
            '''
                <xpath expr="//InvoiceTypeCode" position="attributes">
                    <attribute name="listID">1001</attribute>
                </xpath>
                <xpath expr="//Note[1]" position="after">
                    <Note languageLocaleID="2006">Leyenda: Operacion sujeta a detraccion</Note>
                </xpath>
                <xpath expr="//PaymentTerms" position="replace"/>
                <xpath expr="//AccountingCustomerParty" position="after">
                    <PaymentMeans>
                        <ID>Detraccion</ID>
                        <PaymentMeansCode>999</PaymentMeansCode>
                        <PayeeFinancialAccount>
                            <ID>CUENTAPRUEBA</ID>
                        </PayeeFinancialAccount>
                    </PaymentMeans>
                    <PaymentTerms>
                        <ID>Detraccion</ID>
                        <PaymentMeansID>001</PaymentMeansID>
                        <PaymentPercent>10.0</PaymentPercent>
                        <Amount currencyID="PEN">472.00</Amount>
                    </PaymentTerms>
                    <PaymentTerms>
                        <ID>FormaPago</ID>
                        <PaymentMeansID>Credito</PaymentMeansID>
                        <Amount currencyID="USD">8496.00</Amount>
                    </PaymentTerms>
                    <PaymentTerms>
                        <ID>FormaPago</ID>
                        <PaymentMeansID>Cuota001</PaymentMeansID>
                        <Amount currencyID="USD">1888.00</Amount>
                        <PaymentDueDate>2017-01-01</PaymentDueDate>
                    </PaymentTerms>
                    <PaymentTerms>
                        <ID>FormaPago</ID>
                        <PaymentMeansID>Cuota002</PaymentMeansID>
                        <Amount currencyID="USD">6608.00</Amount>
                        <PaymentDueDate>2017-03-02</PaymentDueDate>
                    </PaymentTerms>
                </xpath>
            ''')
        self.assertXmlTreeEqual(current_etree, expected_etree)

    def test_low_unit_price_with_higher_decimal_precision(self):
        """ Invoice with a decimal precition of 4 digits for the product price
            and a non-zero unit price that is rounded to 0.00 in the decimal
            precision of the currency.
        """
        self.env.ref('product.decimal_price').digits = 4
        self.currency_data['currency'].rounding = 0.01
        with freeze_time(self.frozen_today), \
             patch('odoo.addons.l10n_pe_edi.models.account_edi_format.AccountEdiFormat._l10n_pe_edi_post_invoice_web_service',
                   new=mocked_l10n_pe_edi_post_invoice_web_service):
            invoice_line_vals = {
                'invoice_line_ids': [
                    Command.create({
                        'product_id': self.product.id,
                        'product_uom_id': self.env.ref('uom.product_uom_kgm').id,
                        'price_unit': 0.0045,
                        'quantity': 100,
                        'tax_ids': [Command.set(self.tax_18.ids)],
                    })
                ],
            }
            move = self._create_invoice(**invoice_line_vals)
            move.action_post()

            generated_files = self._process_documents_web_services(move, {'pe_ubl_2_1'})
            zip_edi_str = generated_files[0]
            edi_xml = self.edi_format._l10n_pe_edi_unzip_edi_document(zip_edi_str)

            current_etree = self.get_xml_tree_from_string(edi_xml)
            expected_etree = self.get_xml_tree_from_string(self.expected_invoice_xml_values)
            expected_etree = self.with_applied_xpath(
                expected_etree,
                '''
                    <xpath expr="//Note" position="replace">
                        <Note languageLocaleID="1000">CERO Y 53/100 GOLD</Note>
                    </xpath>
                    <xpath expr="/Invoice/TaxTotal" position="replace">
                        <TaxTotal>
                            <TaxAmount currencyID="USD">0.08</TaxAmount>
                            <TaxSubtotal>
                                <TaxableAmount currencyID="USD">0.45</TaxableAmount>
                                <TaxAmount currencyID="USD">0.08</TaxAmount>
                                <TaxCategory>
                                    <TaxScheme>
                                        <ID>1000</ID>
                                        <Name>IGV</Name>
                                        <TaxTypeCode>VAT</TaxTypeCode>
                                    </TaxScheme>
                                </TaxCategory>
                            </TaxSubtotal>
                        </TaxTotal>
                    </xpath>
                    <xpath expr="//LegalMonetaryTotal" position="replace">
                        <LegalMonetaryTotal>
                            <LineExtensionAmount currencyID="USD">0.45</LineExtensionAmount>
                            <TaxInclusiveAmount currencyID="USD">0.53</TaxInclusiveAmount>
                            <PayableAmount currencyID="USD">0.53</PayableAmount>
                        </LegalMonetaryTotal>
                    </xpath>
                    <xpath expr="//InvoiceLine" position="replace">
                        <InvoiceLine>
                            <ID>1</ID>
                            <InvoicedQuantity unitCode="KGM">100.0</InvoicedQuantity>
                            <LineExtensionAmount currencyID="USD">0.45</LineExtensionAmount>
                            <PricingReference>
                                <AlternativeConditionPrice>
                                    <PriceAmount currencyID="USD">0.0053</PriceAmount>
                                    <PriceTypeCode>01</PriceTypeCode>
                                </AlternativeConditionPrice>
                            </PricingReference>
                            <TaxTotal>
                                <TaxAmount currencyID="USD">0.08</TaxAmount>
                                <TaxSubtotal>
                                    <TaxableAmount currencyID="USD">0.45</TaxableAmount>
                                    <TaxAmount currencyID="USD">0.08</TaxAmount>
                                    <TaxCategory>
                                        <Percent>18.0</Percent>
                                        <TaxExemptionReasonCode>10</TaxExemptionReasonCode>
                                        <TaxScheme>
                                            <ID>1000</ID>
                                            <Name>IGV</Name>
                                            <TaxTypeCode>VAT</TaxTypeCode>
                                        </TaxScheme>
                                    </TaxCategory>
                                </TaxSubtotal>
                            </TaxTotal>
                            <Item>
                                <Description>product_pe</Description>
                                <CommodityClassification>
                                    <ItemClassificationCode>01010101</ItemClassificationCode>
                                </CommodityClassification>
                            </Item>
                            <Price>
                                <PriceAmount currencyID="USD">0.0045</PriceAmount>
                            </Price>
                        </InvoiceLine>
                    </xpath>
                ''')
            self.assertXmlTreeEqual(current_etree, expected_etree)
