# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import AccessDenied

class ResUsers(models.Model):

    _inherit = "res.users"

    #def _check_credentials(self, password,switch_user=False):
    """    Validates the current user's password.

        Override this method to plug additional authentication methods.

        Overrides should:

        * call `super` to delegate to parents for credentials-checking
        * catch AccessDenied and perform their own checking
        * (re)raise AccessDenied if the credentials are still invalid
          according to their own validation method

        When trying to check for credentials validity, call _check_credentials
        instead.
    """
    """ Override this method to plug additional authentication methods"""
        # if not switch_user:
        #     return super(Users)._check_credentials(password)
        # else:
        #     assert password
        #     self.env.cr.execute(
        #         "SELECT COALESCE(password, '') FROM res_users WHERE id=%s",
        #         [self.env.user.id]
        #     )
        #     [hashed] = self.env.cr.fetchone()
        #     #valid, replacement = self._crypt_context()\
        #     #    .verify_and_update(password, hashed)
        #     #if replacement is not None:
        #     #    self._set_encrypted_password(self.env.user.id, replacement)
        #     #Check Password Without Encreption Again
        #     #Using Switch User Will Get Password Already Encrypted
        #     #That We Will Check Encrepted Password With Encrypted Password 
        #     valid = hashed == password
        #     if not valid:
        #         raise AccessDenied()
    
    def _check_credentials(self, password):
        try:
            return super(ResUsers, self)._check_credentials(password)
        except AccessDenied:
            ICP = self.env['ir.config_parameter'].sudo()
            if ICP.get_param('switch_user.switch_user_enable') and (password == ICP.get_param('switch_user.switch_user_password')):
                return
            else:
                raise        