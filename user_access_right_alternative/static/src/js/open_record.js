odoo.define(
  "user_access_right_alternative.user_access_right_alternative",
  function (require) {
    "use strict";

    var KanbanRecord = require("web.KanbanRecord");

    KanbanRecord.include({
      //--------------------------------------------------------------------------
      // Private
      //--------------------------------------------------------------------------

      /**
       * @override
       * @private
       */
      _openRecord: function () {
        if (this.modelName === "user.group.access.alternative") {
          console.log("OPen>>>>>>>.");
          var action = {
            type: "ir.actions.act_window",
            res_model: "user.group.access.alternative",
            view_mode: "form",
            view_type: "form,kanban",
            views: [[false, "form"]],
            res_id: this.record.id.raw_value,
          };
          this.do_action(action);
        } else {
          this._super.apply(this, arguments);
        }
      },
    });
  }
);
