odoo.define("switch_user.UserMenu", function (require) {
  "use strict";

  var core = require("web.core");
  var framework = require("web.framework");
  var Dialog = require("web.Dialog");
  var Widget = require("web.Widget");
  var session = require("web.session");
  var Menu = require("web.WebClient");

  var _t = core._t;
  var QWeb = core.qweb;

  var UserMenu = require("web.UserMenu");

  UserMenu.include({
    _searchUserFetch: function (searchVal, limit) {
      let domain = [["name", "ilike", searchVal]];
      return this._rpc({
        model: "res.users",
        method: "search_read",
        domain: domain,
        fields: ["id", "name", "login", "display_name"],
        limit: limit || 20,
      });
    },

    searchUser: function (searchVal, limit) {
      let def = this._searchUserFetch(searchVal, limit);
      return def.then(function (users) {
        var suggestions = _.map(users, function (user) {
          return {
            id: user.id,
            value: user.name,
            label: user.name,
          };
        });
        return _.sortBy(suggestions, "label");
      });
    },

    _onMenuSwitch_user: function () {
      var self = this;
      var session = this.getSession();

      session.user_context["switch_user"] = true;
      this.trigger_up("clear_uncommitted_changes", {
        callback: function () {
          let $optionsEl =
            '<div class="form-group">\
             <label class="col-form-label"  for="login_user">Password</label>\
              <input type="text" class="o_input o_user_switch_input" id="login_user" name="login_user"/> \
             </div>';
          let passwordEl =
            '<div class="form-group">\
                  <label class="col-form-label"  for="password">Password</label>\
                  <input type="password" class="form-control" id="password" name="password" required="required"/>\
                  </div>';
          var $content = $("<div>").append(
            $(`${$optionsEl} ${passwordEl}</div>`)
          );

          let $partner_input = $content.find(".o_user_switch_input");
          $partner_input.select2({
            width: "100%",
            allowClear: true,
            formatResult: function (item) {
              return $("<span>").text(item.text).prepend("*");
            },
            query: function (query) {
              self.searchUser(query.term, 20).then(function (users) {
                query.callback({
                  results: _.map(users, function (user) {
                    return _.extend(user, { text: user.label });
                  }),
                });
              });
            },
          });

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
                      route: "/web/switch_user/authenticate/",
                      params,
                    })
                    .then(function (result) {
                      if (!result.uid) {
                        return $.Deferred().reject();
                      } else {
                        window.location = result["web.base.url"];
                      }
                    });
                },
              },
              { text: _t("Discard"), close: true },
            ],
            $content: $content,
          }).open();
        },
      });
    },
  });
});
