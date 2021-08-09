odoo.define("switch_user.UserMenu", function (require) {
  "use strict";

  var core = require("web.core");
  var framework = require("web.framework");
  var Dialog = require("web.Dialog");
  var Widget = require("web.Widget");
  var session = require("web.session");

  var _t = core._t;
  var QWeb = core.qweb;

  var UserMenu = require("web.UserMenu");

  UserMenu.include({
    _onMenuSwitch_user: function () {
      var self = this;
      var session = this.getSession();
      console.table("Session################", self);
      this.trigger_up("clear_uncommitted_changes", {
        callback: function () {
          self
            ._rpc({
              model: "res.users",
              method: "search_read",
              args: [],
              fields: ["id", "name", "login", "display_name"],
            })
            .then(function (result) {
              var data = result;
              let $optionsEl =
                '<div class="form-group">\
                <label class="col-form-label"  for="login_user">User</label>\
                <select id="login_user" name="login_user" \
                class="form-control height-select" required="required"><option value="" selected="selected">Users...</option>';
              _.each(data, (user) => {
                $optionsEl += `<option login="${user.login}" value="${user.id}">${user.display_name} </option>`;
              });
              let passwordEl =
                '<div class="form-group">\
                  <label class="col-form-label"  for="password">Password</label>\
                  <input type="password" class="form-control" id="password" name="password" required="required"/>\
                  </div></div>';
              var $content = $("<div>").append(
                $(`${$optionsEl}</select>${passwordEl}
                </div>`)
              );
              return new Dialog(this, {
                title: _t("Switch User"),
                buttons: [
                  {
                    text: _t("Switch"),
                    classes: "btn-primary",
                    close: true,
                    click: function () {
                      var new_user = this.$content.find("#login_user").val();
                      var password = this.$content.find("#password").val();
                      var user_options = $(
                        "select[name='login_user']:enabled option:not(:first)"
                      );
                      let user_option_value = user_options.filter(
                        "[value =" + new_user + "]"
                      );
                      let params = {
                        db: session.db,
                        login: user_option_value.attr("login"),
                        password: password,
                      };
                      return self
                        ._rpc({
                          route: "/web/session/authenticate",
                          params,
                        })
                        .then(function (result) {
                          console.log("After>>>>>>>>>>>>>", result);
                          if (!result.uid) {
                            return $.Deferred().reject();
                          } else {
                            //delete result.session_id;
                            //return session._session_authenticate(
                            //  session.db,
                            //  user_option_value.attr("login"),
                            //  password
                            //);
                            //FOR USER ACtion
                            /**if (_.isEmpty($.bbq.getState(true))) {
                              return self._rpc({
                                      model: 'res.users',
                                      method: 'read',
                                      args: [session.uid, ["action_id"]],
                                  })
                                  .then(function (result) {
                                      var data = result[0];
                                      if (data.action_id) {
                                          return self.do_action(data.action_id[0]).then(function () {
                                              self.menu.change_menu_section(self.menu.action_id_to_primary_menu_id(data.action_id[0]));
                                          });
                                      } else {
                                          self.menu.openFirstApp();
                                      }
                                  });
                          } else {
                              return self.on_hashchange();
                          } */
                            window.location.reload();
                          }
                        });
                    },
                  },
                  { text: _t("Discard"), close: true },
                ],
                $content: $content,
              }).open();
            });
        },
      });
    },
  });
});
