/** @odoo-module **/

import { _t } from "web.core";
import tour from "web_tour.tour";

const { markup } = owl;

tour.register('planning_tour', {
    sequence: 120,
    'skip_enabled': false,
    url: '/web',
    rainbowManMessage: markup(_t("<b>Congratulations!</b></br> You are now a master of planning.")),
}, [
    {
        trigger: '.o_app[data-menu-xmlid="planning.planning_menu_root"]',
        content: _t("Let's start managing your employees' schedule!"),
        position: 'bottom',
    }, {
        trigger: ".o_gantt_button_add",
        content: _t("Let's create your first <b>shift</b>. <i>Tip: use the (+) shortcut available on each cell of the Gantt view to save time.</i>"),
        position: "bottom",
        mobile: false,
    }, {
        trigger: ".o-kanban-button-new",
        content: _t("Let's create your first <b>shift</b>. <i>Tip: use the (+) shortcut available on each cell of the Gantt view to save time.</i>"),
        position: "bottom",
        mobile: true,
    }, {
        trigger: ".o_field_widget[name='resource_id']",
        extra_trigger: ".o_form_view",
        content: _t("Assign a <b>resource</b>, or leave it open for the moment. <i>Tip: Create open shifts for the roles you will be needing to complete a mission. Then, assign those open shifts to the resources that are available.</i>"),
        position: "right",
        run() {
            document.querySelector('.o_field_widget[name="resource_id"] input').click();
        },
    }, {
        trigger: ".o_kanban_record",
        content: _t("Select a resource for the shift"),
        position: "bottom",
        mobile: true,
    }, {
        trigger: ".o_field_widget[name='role_id'] .o_field_many2one_selection",
        content: _t("Write the <b>role</b> your employee will perform (<i>e.g. Chef, Bartender, Waiter, etc.</i>). <i>Tip: Create open shifts for the roles you will be needing to complete a mission. Then, assign those open shifts to the resources that are available.</i>"),
        position: "right",
        run() {
            document.querySelector('.o_field_widget[name="role_id"] input').click();
        },
    }, {
        trigger: ".modal-dialog button.o_create_button",
        content: _t("Let's create a role for the shift"),
        position: "bottom",
        mobile: true,
    }, {
        trigger: ".o_field_widget[name='name'] input",
        content: _t('Write the role your employee will perform (e.g. Chef, Bartender, Waiter, etc.). <i>Tip: Create open shifts for the roles you will be needing to complete a mission. Then, assign those open shifts to the resources that are available.</i>'),
        position: "bottom",
        mobile: true,
    }, {
        trigger: ".modal-footer .o_form_button_save",
        content: _t("Save the role."),
        position: "bottom",
        mobile: true,
    }, {
        trigger: "button[special='save']",
        content: _t("Save this shift once it is ready."),
        position: "bottom",
        mobile: false,
    }, {
        trigger: ".breadcrumb-item.o_back_button",
        content: _t("Let's go back"),
        position: "bottom",
        mobile: true,
    }, {
        trigger: ".o_switch_view",
        content: _t("Let's switch views"),
        position: "bottom",
        mobile: true,
    }, {
        trigger: "button[data-tooltip='Gantt']",
        content: _t("Let's open the Gantt view to publish the schedule"),
        position: "bottom",
        mobile: true,
    }, {
        trigger: ".o_gantt_pill:not(.o_gantt_consolidated_pill)",
        extra_trigger: '.o_action:not(.o_view_sample_data)',
        content: _t("<b>Drag & drop</b> your shift to reschedule it. <i>Tip: hit CTRL (or Cmd) to duplicate it instead.</i> <b>Adjust the size</b> of the shift to modify its period."),
        position: "bottom",
        run: "drag_and_drop_native .o_gantt_cell:nth-child(6)",
        mobile: false,
    }, {
        trigger: ".o_gantt_button_send_all",
        content: _t("If you are happy with your planning, you can now <b>send</b> it to your employees."),
        position: "bottom",
    }, {
        trigger: "button[name='action_check_emails']",
        content: _t("<b>Publish & send</b> your employee's planning."),
        position: "bottom",
    }, {
        trigger: "button.o_gantt_button_next",
        extra_trigger: "body:not(.modal-open)",
        content: _t("Now that this week is ready, let's get started on <b>next week's schedule</b>."),
        position: "bottom",
    }, {
        trigger: "button.o_gantt_button_copy_previous_week",
        content: _t("Plan all of your shifts in one click by <b>copying the previous week's schedule</b>."),
        position: "bottom",
    },
]);
