odoo.define("switch_user.switchAction", function (require) {
  "use strict";
  var ActionManager = require("web.ActionManager");
  var config = require("web.config");
  var Context = require("web.Context");
  var core = require("web.core");
  var data = require("web.data"); // this will be removed at some point
  var pyUtils = require("web.py_utils");
  var SearchView = require("web.SearchView");
  var view_registry = require("web.view_registry");
  var ajax = require('web.ajax');


  var _t = core._t;

  var includeDict = {
    /**
     * Handler for event 'execute_action', which is typically called when a
     * button is clicked. The button may be of type 'object' (call a given
     * method of a given model) or 'action' (execute a given action).
     * Alternatively, the button may have the attribute 'special', and in this
     * case an 'ir.actions.act_window_close' is executed.
     *
     * @private
     * @param {OdooEvent} ev
     * @param {Object} ev.data.action_data typically, the html attributes of the
     *   button extended with additional information like the context
     * @param {Object} [ev.data.action_data.special=false]
     * @param {Object} [ev.data.action_data.type] 'object' or 'action', if set
     * @param {Object} ev.data.env
     * @param {function} [ev.data.on_closed]
     * @param {function} [ev.data.on_fail]
     * @param {function} [ev.data.on_success]
     */
    _onExecuteAction: function () {
      console.log("inherit?????????????", arguments);
      this._super.apply(this, arguments);
      var actionData = ev.data.action_data;
      var env = ev.data.env;
      if (actionData.type === "switch" && env.model === "switch.user") {
        
        self._rpc({
          route: '/switch_user/switch_user/',
          params: {
              user: currentAction.id ,
              //password: c,
              
          },
      })
      .then(function (r) {
          if (r) {
              self.do_notify(
                  _.str.sprintf(_t("'%s' added to dashboard"), name),
                  _t('Please refresh your browser for the changes to take effect.')
              );
          } else {
              self.do_warn(_t("Could not add filter to dashboard"));
          }
      });

      }
    },
  };

  ActionManager.include(includeDict);
});
