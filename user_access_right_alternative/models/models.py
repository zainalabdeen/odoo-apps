# -*- coding: utf-8 -*-

import re
from odoo import models, fields, api,_
from odoo.exceptions import UserError, ValidationError
from lxml.builder import E
from lxml import etree
from odoo.addons.base.models import res_users
from odoo.tools import partition, pycompat, collections
from itertools import chain, repeat
import itertools
from collections import defaultdict


class userGroupAccessAlternative(models.Model):
    _name = 'user.group.access.alternative'

    origin_user_id = fields.Many2one('res.users',required=True)
    alternate_user_id = fields.Many2one('res.users',required=True)
    origin_group_ids = fields.Many2many('res.groups','access_alternate_origin_groups','origin_user_id','group_id')
    new_group_ids = fields.Many2many('res.groups','access_alternate_new_groups','new_user_id','new_group_id')
    state = fields.Selection([('draft','Draft'),('start_granted','Start Granted'),
                            ('stop_granted','Stop Granted')],default="draft")
    new_groups_count = fields.Integer(compute='_get_group_count',store=True)

    def get_groups(self):
        for rec in self:
            rec.origin_group_ids = rec.origin_user_id.groups_id - rec.alternate_user_id.groups_id
            rec.new_group_ids = rec.origin_user_id.groups_id - rec.alternate_user_id.groups_id
            if not rec.new_group_ids:
                raise ValidationError(_('Sorry ,Those Two Users Have The Same Access,No Different Between Them to Grant'))
            return {'type': 'ir.actions.client', 'tag': 'reload'}    

    def start_granted(self):
        for rec in self:
            rec.alternate_user_id.groups_id += rec.new_group_ids
            rec.write({'state':'start_granted'})

    def stop_granted(self):
        for rec in self:
            rec.alternate_user_id.groups_id -= rec.new_group_ids
            rec.write({'state':'stop_granted'})

    def set_to_draft(self):
        for rec in self:
            rec.stop_granted()
            rec.new_group_ids = False
            rec.origin_group_ids = False
            rec.write({'state':'draft'})                    

    @api.depends('origin_group_ids')
    def _get_group_count(self):
        for rec in self:
            rec.new_groups_count = len(rec.origin_group_ids)      

    @api.model
    def fields_get(self, allfields=None, attributes=None):
        res = super(userGroupAccessAlternative, self).fields_get(allfields, attributes=attributes)
        # add reified groups fields
        for app, kind, gs in self.get_groups_by_application():
            # boolean group fields
            for g in gs:
                field_name = res_users.name_boolean_group(g.id)
                if allfields and field_name not in allfields:
                    continue
                res[field_name] = {
                    'type': 'boolean',
                    'string': g.name,
                    'help': g.comment,
                    'exportable': False,
                    'selectable': False,
                }
        return res

    #################New Functions#########################




    @api.multi
    def write(self, values):
        values = self._remove_reified_groups(values)
        res = super(userGroupAccessAlternative, self).write(values)
        group_multi_company = self.env.ref('base.group_multi_company', False)
        if group_multi_company and 'company_ids' in values:
            for user in self:
                if len(user.company_ids) <= 1 and user.id in group_multi_company.users.ids:
                    user.write({'new_group_ids': [(3, group_multi_company.id)]})
                elif len(user.company_ids) > 1 and user.id not in group_multi_company.users.ids:
                    user.write({'new_group_ids': [(4, group_multi_company.id)]})
        return res


    def _remove_reified_groups(self, values):
        """ return `values` without reified group fields """
        add, rem = [], []
        values1 = {}

        for key, val in values.items():
            if res_users.is_boolean_group(key):
                (add if val else rem).append(res_users.get_boolean_group(key))
            elif res_users.is_selection_groups(key):
                rem += res_users.get_selection_groups(key)
                if val:
                    add.append(val)
            else:
                values1[key] = val

        if 'new_group_ids' not in values and (add or rem):
            # remove group ids in `rem` and add group ids in `add`
            values1['new_group_ids'] = list(itertools.chain(
                pycompat.izip(repeat(3), rem),
                pycompat.izip(repeat(4), add)
            ))

        return values1

    @api.multi
    def read(self, fields=None, load='_classic_read'):
        # determine whether reified groups fields are required, and which ones
        fields1 = fields or list(self.fields_get())
        group_fields, other_fields = partition(res_users.is_reified_group, fields1)

        # read regular fields (other_fields); add 'groups_id' if necessary
        drop_groups_id = False
        if group_fields and fields:
            if 'new_group_ids' not in other_fields:
                other_fields.append('new_group_ids')
                drop_groups_id = True
        else:
            other_fields = fields

        res = super(userGroupAccessAlternative, self).read(other_fields, load=load)

        # post-process result to add reified group fields
        if group_fields:
            for values in res:
                self._add_reified_groups(group_fields, values)
                if drop_groups_id:
                    values.pop('new_group_ids', None)
        return res

    def _add_reified_groups(self, fields, values):
        """ add the given reified group fields into `values` """
        gids = set(res_users.parse_m2m(values.get('new_group_ids') or []))
        for f in fields:
            if res_users.is_boolean_group(f):
                values[f] = res_users.get_boolean_group(f) in gids
            elif res_users.is_selection_groups(f):
                selected = [gid for gid in res_users.get_selection_groups(f) if gid in gids]
                # if 'Internal User' is in the group, this is the "User Type" group
                # and we need to show 'Internal User' selected, not Public/Portal.
                if self.env.ref('base.group_user').id in selected:
                    values[f] = self.env.ref('base.group_user').id
                else:
                    values[f] = selected and selected[-1] or False


    @api.model
    def _fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        res = super(userGroupAccessAlternative, self)._fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar, submenu=submenu)
        print("Field VIEW Child Model1>>>>>>>>>>>>>>>>>")
        if view_type == 'form':
            doc = etree.XML(res['arch'])
            record_id = False
            if self._context.get('params',False) and self._context.get('params').get('id',False):   
                record_id = self._context.get('params').get('id')
            elif self._context.get('active_id',False):
                record_id = self._context.get('active_id')
            elif self._context.get('active_ids',False):   
                 record_id = self._context.get('active_ids')[0] 
            print("Field VIEW Child Model2>>>>>>>>>>>>>>>>>",self._context.get('params',False),"#",self._context.get('active_id',False),"#",self._context.get('active_ids',False))     
             
            if record_id and self.browse(record_id).origin_group_ids:    
                new_group_str = self._get_groups_view(self.browse(record_id).origin_group_ids)
                new_group_xml = etree.XML(new_group_str)
                if doc.xpath("//field[@name='new_group_ids']"):
                    for group_node in doc.xpath("//field[@name='new_group_ids']"):
                        group_node.getparent().replace(group_node,new_group_xml)
                    res['arch'] = etree.tostring(doc, encoding='unicode')
        return res        


    @api.multi
    def get_formview_action(self, access_uid=None):
        """ Return an action to open the document ``self``. This method is meant
            to be overridden in addons that want to give specific view ids for
            example.

        An optional access_uid holds the user that will access the document
        that could be different from the current user. """
        view_id = self.sudo().get_formview_id(access_uid=access_uid)
        return {
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'view_type': 'form',
            'view_mode': 'form',
            'views': [(view_id, 'form')],
            'target': 'current',
            'res_id': self.id,
            'context': dict(self._context),
        }
        
    @api.model
    def _get_groups_view(self,group_ids=[]):
        """ Modify the view with xmlid ``base.user_groups_view``, which inherits
            the user form view, and introduces the reified group fields.
        """
        # remove the language to avoid translations, it will be handled at the view level
        self = self.with_context(lang=None)

        xml1, xml2, xml3 = [], [], []
        user_group_attrs = {'invisible': [('new_groups_count', '<', 1)]}

        sorted_triples = sorted(self.get_groups_by_application(group_ids),
                                key=lambda t: t[0].xml_id != 'base.module_category_user_type')
        for app, kind, gs in sorted_triples:  # we process the user type first
            attrs = {}
            # hide groups in categories 'Hidden' and 'Extra' (except for group_no_one)
            if app.xml_id in ('base.module_category_hidden', 'base.module_category_extra', 'base.module_category_usability'):
                attrs['groups'] = 'base.group_no_one'


            # application separator with boolean fields
            app_name = app.name or 'Other'
            xml3.append(E.separator(string=app_name, colspan="4", **attrs))
            for g in gs:
                field_name = res_users.name_boolean_group(g.id)
                xml3.append(E.field(name=field_name, **attrs))

        xml3.append({'class': "o_label_nowrap"})

        xml = E.group(
            E.group(*(xml1), col="2"),
            E.group(*(xml2), col="2", attrs=str(user_group_attrs)),
            E.group(*(xml3), col="4", attrs=str(user_group_attrs)),attrs=str(user_group_attrs))
        xml.addprevious(etree.Comment("GENERATED AUTOMATICALLY BY GROUPS"))
        xml_content = etree.tostring(xml, pretty_print=True, encoding="unicode")
        return xml_content



    def get_application_groups(self, domain):
        """ Return the non-share groups that satisfy ``domain``. """
        return self.env['res.groups'].search(domain + [('share', '=', False)])

    def get_groups_by_application(self,group_ids=[]):
        """ Return all groups classified by application (module category), as a list::

                [(app, kind, groups), ...],

            where ``app`` and ``groups`` are recordsets, and ``kind`` is either
            ``'boolean'`` or ``'selection'``. Applications are given in sequence
            order.  If ``kind`` is ``'selection'``, ``groups`` are given in
            reverse implication order.
        """
        domain = []
        if len(group_ids):
            domain += [('id','in',group_ids.ids)]
        def linearize(app, gs):
            # determine sequence order: a group appears after its implied groups
            order = {g: len(g.trans_implied_ids & gs) for g in gs}
            return (app, 'boolean', gs)

        # classify all groups by application
        by_app, others = defaultdict(self.env['res.groups'].browse), self.env['res.groups'].browse()
        for g in self.get_application_groups(domain):
            if g.category_id:
                by_app[g.category_id] += g
            else:
                others += g
        # build the result
        res = []
        for app, gs in sorted(by_app.items(), key=lambda it: it[0].sequence or 0):
            res.append(linearize(app, gs))
        if others:
            res.append((self.env['ir.module.category'], 'boolean', others))
        return res

    @api.multi
    def get_form_view(self):
        self.clear_caches()
        print("************IN KANBAN**********")
        action_rec = self.env.ref('user_access_right_alternative.user_access_right_alternative_action_window')
        action = action_rec.read()[0]
        ctx = dict(self.env.context)
        action['context'] = ctx
        ctx['active_id'] = self.id
        ctx['active_ids'] = self.ids
        if self._context.get('params',False):
            if self._context.get('params').get('id',False):
                ctx['params']['id'] =  self.id
            if self._context.get('params').get('active_id',False):
                ctx['params']['active_id'] =  self.id
            if self._context.get('params').get('active_ids',False):
                ctx['params']['active_ids'] =  self.ids       
        action['view_mode'] = 'form'
        action['res_id'] = self.id
        action['views'] = [(self.env.ref('user_access_right_alternative.user_group_access_alternative_form').id, 'form')]
        print("**********",action)
        return action
