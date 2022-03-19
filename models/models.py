# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import datetime
from datetime import date
from odoo.exceptions import UserError
from odoo.tools.translate import _

class TravelAdvanceRequest(models.Model):
    _name = 'travel_advance.process'
    _rec_name = 'request_no'
    _description = 'Table for handling travel request '
    _inherit = ['mail.thread', 'mail.activity.mixin']

    request_no = fields.Char(string="Request Number", default=lambda self: _('New'), requires=False, readonly=True,
                             trace_visibility='onchange', )
    request_date = fields.Datetime(string="Date/Time of request", required=False, default=lambda self: fields.datetime.now())
    traveller_name = fields.Many2one('res.users', 'Requesting User', readonly=True, default=lambda self: self.env.user.id)
    # traveller_name = fields.Char(string="Name of Traveller", required=False, )
    travel_date = fields.Date(string="Date of Travel", required=False, )
    destination = fields.Char(string="Organisation/Destination", required=False,)
    traveller_address = fields.Text(string="Traveller Address", required=False, )
    grade_level = fields.Selection(string="Grade Level", selection=[('Grade Level 1', 'Grade Level 1'), ('Grade Level 2', 'Grade Level 2'), ], required=False, )
    travel_details_ids = fields.One2many(comodel_name="travel.details", inverse_name="travel_request_id",
                                         string="Travel Details", required=False, )
    amount_total = fields.Float('Total', compute='_amount_total', store=True)
    justification = fields.Text(string="Justification", required=False, )
    state = fields.Selection(string="",
                             selection=[('draft', 'draft'), ('Requested', 'Requested'), ('HOD Approve', 'HOD Approval'),
                                        ('Fin Approve', 'Fin Approved'),  ('process', 'Processed'),
                                        ('Rejected', 'Rejected'), ], required=False, copy=False, default='draft',
                             readonly=True, track_visibility='onchange', )
    active = fields.Boolean(
        string='Active',
        required=False, default=True)
    memo_to = fields.Many2one(comodel_name="res.users", string="TO", required=True,
                              domain=lambda self: [
                                  ("groups_id", "=", self.env.ref("nbet.hod_group").id)])
    voucher_obj = fields.Many2one('payment_voucher.ebs', invisible=1)

    @api.model
    def create(self, vals):
        if vals.get('request_no', _('New')) == _('New'):
            vals['request_no'] = self.env['ir.sequence'].next_by_code('increment_travel_request') or _('New')
        result = super(TravelAdvanceRequest, self).create(vals)
        return result

    @api.one
    @api.depends('travel_details_ids.total', )
    def _amount_total(self):
        self.amount_total = sum(travel_details.total for travel_details in self.travel_details_ids)

    @api.multi
    def is_allowed_transition(self, old_state, new_state):
        allowed = [('draft', 'Requested'),
                   ('Requested', 'HOD Approve'),
                   ('Requested', 'Rejected'),
                   ('HOD Approve', 'Fin Approve'),
                   ('Fin Approve', 'process'),
                   ('HOD Approve', 'Rejected'),
                   ]
        return (old_state, new_state) in allowed

    @api.multi
    def change_state(self, new_state):
        for travel in self:
            if travel.is_allowed_transition(travel.state, new_state):
                travel.state = new_state
            else:
                msg = _('Moving from %s to %s is not allowed') % (travel.state, new_state)
                raise UserError(msg)

    @api.multi
    def travel_advance_request(self):
        self.change_state('Requested')

    @api.multi
    def travel_advance_approve(self):
        self.change_state('HOD Approve')

    @api.multi
    def travel_advance_fin_approve(self):
        self.change_state('Fin Approve')

    @api.multi
    def travel_advance_reject(self):
        self.change_state('Rejected')

    @api.multi
    def travel2_advance_reject(self):
        self.change_state('Rejected')

    @api.multi
    def process(self):
        voucher_obj = self.env['payment_voucher.ebs'].create({'originating_memo': self.request_no,

                                                                  })

        self.voucher_obj = voucher_obj
        for expense_val in self.travel_details_ids:
            advance_details = []
            exp_detail = {'name': expense_val.allowance,
                          'payee_id': self.traveller_name.id,
                          'rate': self.amount_total,
                          'voucher_id': self.voucher_obj.id,
                          }
            advance_details.append(exp_detail)
            self.env['voucher_details.ebs'].create(advance_details)

        self.change_state('process')



class TravelDetails(models.Model):
    _name = 'travel.details'
    _rec_name = 'name'
    _description = 'Hold details of travel request'

    name = fields.Char()
    travel_request_id = fields.Many2one(comodel_name="travel_advance.nbet_process", string="", required=False, )
    location = fields.Char(string="Location", required=False, )
    allowance = fields.Char(string="Allowance", required=False, )
    rates = fields.Float(string="Rates",  required=False, )
    days = fields.Integer(string="Days", required=False, )
    total = fields.Float(string="Total",  required=False, compute='_compute_price_subtotal', store=True, digits=0 )

    @api.one
    @api.depends('rates', 'days',  )
    def _compute_price_subtotal(self):
        self.total = self.rates * self.days


class AdvanceRequest(models.Model):
    _name = 'advance_request.ebs'
    _rec_name = 'request_no'
    _description = 'Table for Advance request'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string="Names")
    memo_to = fields.Many2one(comodel_name="res.users", string="TO", required=True,
                              domain=lambda self: [
                                  ("groups_id", "=", self.env.ref("nbet.hod_group").id)])
    request_no = fields.Char(string="Request Number", default=lambda self: _('New'), requires=False, readonly=True,
                             trace_visibility='onchange', )
    designation = fields.Char(string="Designation", required=False, )
    purpose = fields.Char(string="Purpose of Advance", required=False, )
    date = fields.Date(string="Date of Advance", required=False, )
    advance_details_ids = fields.One2many(comodel_name="advance_details.ebs", inverse_name="advance_request_id",
                                         string="Advance Details", required=False, )
    amount_total = fields.Monetary('Total Amount', compute='_amount_total', store=True)
    state = fields.Selection(string="",
                             selection=[('draft', 'draft'), ('Requested', 'Requested'), ('HOD Approve', 'HOD Approval'),
                                        ('FC Approve', 'FC Approved'), ('CFOApprove', 'CFO Approved'),
                                        ('CEO Approve', 'CEO Approved'), ('CFOForward', 'CFO Forward'),
                                        ('Input Details', 'Input Details'), ('Review Details', 'Review Details'),
                                        ('process', 'Processed'),
                                        ('Rejected', 'Rejected'), ], required=False, copy=False, default='draft',
                             readonly=True, track_visibility='onchange', )
    deptal_no = fields.Char(string="Deptal Number", required=False, )
    payee = fields.Char(string="Payee", required=False, )
    payee_id = fields.Many2one('res.partner', string='Payee', track_visibility='onchange', readonly=True,
                               states={'draft': [('readonly', False)], 'Input Details': [('readonly', False)]}, )
    class_code = fields.Char(string="Classification Code", required=False, )
    voucher_obj = fields.Many2one('payment_voucher.ebs', invisible=1)
    company_id = fields.Many2one('res.company', string='', required=True, readonly=True,
                                 default=lambda self: self.env.user.company_id)
    currency_id = fields.Many2one('res.currency', compute='_compute_currency', store=True, string="Currency")
    current_user = fields.Many2one('res.users', 'Current User', default=lambda self: self.env.user)

    @api.one
    @api.depends('company_id')
    def _compute_currency(self):
        self.currency_id = self.company_id.currency_id or self.env.user.company_id.currency_id

    @api.one
    @api.depends('advance_details_ids.amount', )
    def _amount_total(self):
        self.amount_total = sum(advance_details.amount for advance_details in self.advance_details_ids)

    @api.model
    def create(self, vals):
        if vals.get('request_no', _('New')) == _('New'):
            vals['request_no'] = self.env['ir.sequence'].next_by_code('increment_staff_advance') or _('New')
        result = super(AdvanceRequest, self).create(vals)
        return result

    @api.multi
    def is_allowed_transition(self, old_state, new_state):
        allowed = [('draft', 'Requested'),
                   ('Requested', 'HOD Approve'),
                   ('Requested', 'Rejected'),
                   ('HOD Approve', 'FC Approve'),
                   ('FC Approve', 'CFOApprove'),
                   ('HOD Approve', 'Rejected'),
                   ('CFOApprove', 'CEO Approve'),
                   ('CEO Approve', 'CFOForward'),
                   ('CFOForward', 'Input Details'),
                   ('CFOForward', 'CEO Approve'),
                   ('Input Details', 'Review Details'),
                   ('Review Details', 'process'),
                   ('FC Approved', 'Rejected'),
                   ('FC Approve', 'CFOForward'),
                   ('CFOApproved', 'Rejected'),
                   ]
        return (old_state, new_state) in allowed

    @api.multi
    def change_state(self, new_state):
        for advance in self:
            if advance.is_allowed_transition(advance.state, new_state):
                advance.state = new_state
            else:
                msg = _('Moving from %s to %s is not allowed') % (advance.state, new_state)
                raise UserError(msg)

    @api.multi
    def staff_advance_request(self):
        self.change_state('Requested')

    @api.multi
    def staff_advance_hod_approve(self):
        self.change_state('HOD Approve')

    @api.multi
    def staff_advance_fc_approve(self):
        self.change_state('FC Approve')

    @api.multi
    def staff_advance_ceo_approve(self):
        self.change_state('CEO Approve')

    @api.multi
    def staff_advance_cfo_approve(self):
        if self.amount_total > self.current_user.partner_id.advance_limit:
            msg = _('The Cash advance amount is above your approval limit')
            raise UserError(msg)
        else:
            self.change_state('CFOApprove')

    @api.multi
    def request_ceo_approval(self):
        self.change_state('CFOForward')

    @api.multi
    def staff_advance_input_details(self):
        self.change_state('Input Details')

    @api.multi
    def staff_advance_review_details(self):
        self.change_state('Review Details')

    @api.multi
    def staff_advance_cfo_forward(self):
        self.change_state('CFOForward')

    @api.multi
    def staff2_advance_reject(self):
        self.change_state('Rejected')

    @api.multi
    def process(self):
        voucher_obj = self.env['payment_voucher.ebs'].create({'originating_memo': self.request_no,

                                                              })
        self.voucher_obj = voucher_obj
        for expense_val in self.advance_details_ids:
            advance_details = []
            exp_detail = {'name': expense_val.description,
                          'payee_id': self.payee_id.id,
                          'rate': expense_val.amount,
                          'voucher_id': self.voucher_obj.id,
                           }
            advance_details.append(exp_detail)
            self.env['voucher_details.ebs'].create(advance_details)

        self.change_state('process')


class AdvanceDetails(models.Model):
    _name = 'advance_details.ebs'
    _rec_name = 'name'
    _description = 'Table for details of advance'

    name = fields.Char()
    description = fields.Char(string="Description", required=False, )
    amount = fields.Float(string="Amount",  required=False, )
    advance_request_id = fields.Many2one(comodel_name="advance_request.ebs", string="", required=False, )


class ResPartner(models.Model):
    _inherit = 'res.partner'

    advance_limit = fields.Monetary('Advance approval limit',)
    company_id = fields.Many2one('res.company', string='', required=True, readonly=True,
                                 default=lambda self: self.env.user.company_id)
    currency_id = fields.Many2one('res.currency', compute='_compute_currency', store=True, string="Currency")

    @api.one
    @api.depends('company_id')
    def _compute_currency(self):
        self.currency_id = self.company_id.currency_id or self.env.user.company_id.currency_id

# class ebs_process(models.Model):
#     _name = 'ebs_process.ebs_process'

#     name = fields.Char()
#     value = fields.Integer()
#     value2 = fields.Float(compute="_value_pc", store=True)
#     description = fields.Text()
#
#     @api.depends('value')
#     def _value_pc(self):
#         self.value2 = float(self.value) / 100