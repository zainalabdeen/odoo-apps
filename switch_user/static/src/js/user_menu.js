odoo.define("switch_user.UserMenu", function (require) {
  "use strict";

  var core = require("web.core");
  var framework = require("web.framework");
  var Dialog = require("web.Dialog");
  var Widget = require("web.Widget");

  var _t = core._t;
  var QWeb = core.qweb;

  var UserMenu = require("web.UserMenu");

  UserMenu.include({
    _onMenuSwitch_user: function () {
      var self = this;
      console.log("############",self)
      var session = this.getSession();
      this.trigger_up("clear_uncommitted_changes", {
        callback: function () {
          //self.do_action("switch_user.action_res_users_switch");
          self._rpc({
            model: 'res.users',
            method: 'search_read',
            args: [],
        })
        .then(function (result) {
          var data = result;

          console.log("%%%%%%%%%%%%%%",data);
          let $optionsEl = '<select id="login_user" name="login_user" \
          class="form-control height-select"><option value="" selected="selected">Users...</option>' ;
          _.each(data,(user)=> {
            $optionsEl += `<option value="${user.id}">${user.display_name} </option>`;
          });
          var $content = $('<div>').append($(`${$optionsEl}</select></div>`));

          return new Dialog(this, {
              title: _t('Switch User'),
              buttons: [{text: _t('Switch'), classes: 'btn-primary', close: true, click: function () {
                  var new_user = this.$content.find('#login_user').val();
                  console.log("**********",new_user);
                  return self._rpc({
                    route: '/switch_user/switch_user/',
                    params: {
                        user: new_user ,
                        //password: c,
                        
                    },
                }).then(function (result) {
                  console.log("After>>>>>>>",result);
                      self.update({}, {reload: false});
                  });
              }}, {text: _t('Discard'), close: true}],
              $content: $content,
          }).open();


        });

        },
      });
    },
  });
});
