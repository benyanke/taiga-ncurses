# -*- coding: utf-8 -*-

"""
gmncurses.ui.widgets
~~~~~~~~~~~~~~~~~~~~
"""

import urwid
from x256 import x256

from gmncurses import data
from gmncurses.ui import mixins


def box_solid_fill(char, height):
    sf = urwid.SolidFill(char)
    return urwid.BoxAdapter(sf, height=height)


def wrap_in_whitespace(widget, cls=urwid.Columns):
    whitespace = urwid.SolidFill(" ")
    return cls([whitespace, widget, whitespace])


def center(widget):
    return wrap_in_whitespace(wrap_in_whitespace(widget), cls=urwid.Pile)


def banner():
    bt = urwid.BigText("GreenMine", font=urwid.font.HalfBlock7x7Font())
    btwp = urwid.Padding(bt, "center", width="clip")
    return urwid.AttrWrap(btwp, "green")


def username_prompt(username_text, editor, max_prompt_padding):
    username = urwid.Text(username_text, "center")
    return urwid.Columns([(len(username_text), username),
                          (max_prompt_padding - len(username_text), urwid.Text("")),
                          urwid.AttrWrap(editor, "editor")])


def password_prompt(password_text, editor, max_prompt_padding):
    password = urwid.Text(password_text, "center")
    return urwid.Columns([(len(password_text), password),
                          (max_prompt_padding - len(password_text), urwid.Text("")),
                          urwid.AttrWrap(editor, "password-editor")])


def wrap_login_button(button):
    return urwid.AttrWrap(urwid.LineBox(button), "save-button")


def button(text, align=None):
    return PlainButton(text.upper(), align)


def editor(mask=None):
    if mask is None:
        return urwid.Edit()
    else:
        return urwid.Edit(mask=mask)


class Login(mixins.FormMixin, urwid.ListBox):
    def __init__(self, widgets):
        super(Login, self).__init__(urwid.SimpleListWalker(widgets))


class Notifier(mixins.NotifierMixin, mixins.NonSelectableMixin, urwid.Text):
    pass


class PlainButton(mixins.PlainButtonMixin, urwid.Button):
    ALIGN = "center"

    def __init__(self, text, align=None):
        super().__init__(text)
        self._label.set_align_mode(self.ALIGN if align is None else align)

class SubmitButton(PlainButton):
    def __init__(self, text, align=None):
        super().__init__(text, align)

class CancelButton(PlainButton):
    def __init__(self, text, align=None):
        super().__init__(text, align)



class ProjectsHeader(mixins.NonSelectableMixin, urwid.WidgetWrap):
    def __init__(self):
        text = urwid.Text("GREENMINE")
        self.account_button = PlainButton("My account")
        cols = urwid.Columns([
            ("weight", 0.9, text),
            ("weight", 0.1, urwid.AttrMap(self.account_button, "account-button")),
        ])
        super().__init__(urwid.AttrMap(cols, "green-bg"))


class FooterNotifier(Notifier):
    ALIGN = "left"
    ERROR_PREFIX = "[ERROR]: "
    ERROR_ATTR = "footer-error"
    INFO_PREFIX = "[INFO]: "
    INFO_ATTR = "footer-info"


class Footer(mixins.NonSelectableMixin, urwid.WidgetWrap):
    def __init__(self, notifier):
        assert isinstance(notifier, FooterNotifier)
        cols = urwid.Columns([
            ("weight", 0.9, urwid.AttrMap(notifier, "footer")),
            ("weight", 0.1, urwid.AttrMap(PlainButton("? Help"), "help-button")),
        ])
        super().__init__(cols)


class ProjectDetailHeader(mixins.NonSelectableMixin, urwid.WidgetWrap):
    def __init__(self, project):
        text = urwid.Text("GREENMINE")
        self.title = urwid.Text(project["name"], align="left")
        self.projects_button = PlainButton("My projects")
        self.account_button = PlainButton("My account")
        cols = urwid.Columns([
            ("weight", 0.1, text),
            ("weight", 0.7, self.title),
            ("weight", 0.1, urwid.AttrMap(self.projects_button, "projects-button")),
            ("weight", 0.1, urwid.AttrMap(self.account_button, "account-button")),
        ])
        super().__init__(urwid.AttrMap(cols, "green-bg"))


class Grid(mixins.ViMotionMixin, mixins.EmacsMotionMixin, urwid.GridFlow):
    pass


class Tabs(mixins.NonSelectableMixin, urwid.WidgetWrap):
    def __init__(self, tabs, focus=0):
        self.tab_list = urwid.MonitoredFocusList(tabs)
        self.tab_list.focus = focus
        self.tab_list.set_focus_changed_callback(self.rebuild_tabs)

        cols = [urwid.AttrMap(self.tab(t), "active-tab" if i == self.tab_list.focus else "inactive-tab")
                                for i, t in enumerate(tabs)]
        self.columns = urwid.Columns(cols)

        super().__init__(self.columns)

    def rebuild_tabs(self, new_focus):
        for i, c in enumerate(self.columns.contents):
            widget, _ = c
            widget.set_attr_map({None: "active-tab" if i == new_focus  else "inactive-tab"})

    def tab(self, text):
        return urwid.LineBox(urwid.Text(text + " "))


class ProjectBacklogStats(urwid.WidgetWrap):
    def __init__(self, project):
        self.project = project
        widget = urwid.Columns([
            ("weight", 0.3, urwid.Pile([urwid.Text("")])),
            ("weight", 0.3, urwid.Pile([urwid.Text("")])),
            ("weight", 0.3, urwid.Pile([urwid.Text("")])),
        ])
        super().__init__(widget)

    def populate(self, project_stats):
        self._w = urwid.Columns([
            ("weight", 0.2, urwid.Pile([TotalPoints(project_stats), TotalSprints(self.project)])),
            ("weight", 0.3, urwid.Pile([CompletedSprints(self.project), CurrentSprint(self.project)])),
            ("weight", 0.6, urwid.Pile([ClosedPoints(project_stats), DefinedPoints(project_stats), ])),
        ])


class TotalPoints(urwid.Text):
    def __init__(self, project_stats):
        text = ["Total points: ", ("cyan", str(data.total_points(project_stats)))]
        super().__init__(text)


class TotalSprints(urwid.Text):
    def __init__(self, project):
        text = ["Total sprints: ", ("cyan", str(data.total_sprints(project)))]
        super().__init__(text)


class ClosedPoints(urwid.Columns):
    def __init__(self, project_stats, **kwargs):
        text = urwid.Text(["Closed points: ", ("green", str(data.closed_points(project_stats)))])

        progressbar = urwid.ProgressBar("progressbar-normal", "progressbar-complete",
                                        data.closed_points(project_stats), data.total_points(project_stats),
                                        "progressbar-smooth")

        widget_list = [("weight", 0.4, text),
                       ("weight", 0.6, urwid.Padding(progressbar, align='center', left=2, right=2))]
        super().__init__(widget_list, **kwargs)


class DefinedPoints(urwid.Columns):
    def __init__(self, project_stats, **kwargs):
        defined_points_percentage = data.defined_points_percentage(project_stats)
        if defined_points_percentage <= 100.0:
            text = urwid.Text(["Defined points: ", ("red", str(data.defined_points(project_stats)))])
        else:
            text = urwid.Text(["Defined points: ", ("red", str(data.defined_points(project_stats))),
                               " (", ("red", "+{0:.1f} %".format(defined_points_percentage - 100.0)), ")"])

        progressbar = urwid.ProgressBar("progressbar-normal-red", "progressbar-complete-red",
                                        data.defined_points(project_stats), data.total_points(project_stats),
                                        "progressbar-smooth-red")

        widget_list = [("weight", 0.4, text),
                       ("weight", 0.6, urwid.Padding(progressbar, align='center', left=2, right=2))]
        super().__init__(widget_list, **kwargs)


class CurrentSprint(urwid.Text):
    def __init__(self, project):
        text = [
            "Current sprint: ",
            ("cyan", str(data.current_sprint(project))),
            " (",
            ("cyan", str(data.current_sprint_name(project))),
            ")",
        ]
        super().__init__(text)


class CompletedSprints(urwid.Text):
    def __init__(self, project):
        text = ["Completed sprints: ", ("green", str(len(data.completed_sprints(project))))]
        super().__init__(text)


class UserStoryList(mixins.ViMotionMixin, mixins.EmacsMotionMixin, urwid.WidgetWrap):
    def __init__(self, project):
        self.project = project
        self.roles = data.computable_roles(project)

        colum_items = [("weight", 0.6, ListCell("US"))]
        colum_items.append(("weight", 0.08, ListCell("Status")))
        colum_items.extend([("weight", 0.05, ListCell(r["name"])) for r in self.roles.values()])
        colum_items.append(("weight", 0.05, ListCell(("green", "TOTAL"))))
        colum_items.append(("weight", 0.05, ListCell(("cyan", "SUM."))))

        columns = urwid.Columns(colum_items)
        self.widget = urwid.Pile([columns])
        super().__init__(self.widget)

    def populate(self, user_stories, project_stats, set_focus=None):
        if user_stories:
            self.reset()

        self.doomline_limit = data.doomline_limit_points(project_stats)
        first_gains_focus = len(self.widget.contents) == 1 and user_stories

        summation = 0
        doomline = False

        for us in user_stories:
            summation += data.us_total_points(us)

            if not doomline and summation > self.doomline_limit:
                self.widget.contents.append((RowDivider("red", div_char="☠"), ("weight", 0.1)))
                doomline = True

            self.widget.contents.append((UserStoryEntry(us, self.project, self.roles, summation),
                                         ("weight", 0.1)))
        # Set the focus # TODO: Refactor
        if first_gains_focus:
            if set_focus:
                for idx, item in enumerate(self.widget.contents):
                    widget, options = item
                    if type(widget) is UserStoryEntry and widget.user_story == set_focus:
                        self.widget.contents.focus = idx

            if not self.widget.contents.focus:
                self.widget.contents.focus = 1


    def reset(self):
        self.widget.contents = self.widget.contents[:1]


class UserStoryEntry(urwid.WidgetWrap):
    def __init__(self, us, project, roles, summation=0.0):
        self.user_story = us

        us_ref_and_name = "#{0: <6} {1}".format(str(data.us_ref(us)), data.us_subject(us))
        colum_items = [("weight", 0.6, ListText(us_ref_and_name, align="left"))]

        hex_color, status = data.us_status_with_color(us, project)
        color = color_to_hex(hex_color)
        attr = urwid.AttrSpec("h{0}".format(color), "default")
        colum_items.append(("weight", 0.08, ListText( (attr, status) )))

        points_by_role = data.us_points_by_role(us, project, roles.values())
        for point in points_by_role:
            colum_items.append(("weight", 0.05, ListText(str(point))))
        colum_items.append(("weight", 0.05, ListText(("green", "{0:.1f}".format(data.us_total_points(us))))))
        colum_items.append(("weight", 0.05, ListText(("cyan", "{0:.1f}".format(summation)))))

        self.widget = urwid.Columns(colum_items)
        super().__init__(urwid.AttrMap(self.widget, "default", "focus"))

    def selectable(self):
        return True

class UserStoryForm( mixins.FormMixin, urwid.WidgetWrap):
    _status = None
    _points = {}

    def __init__(self, project, user_story={}):
        self.project = project
        self.user_story = user_story

        contents = [
            box_solid_fill(" ", 2),
            self._subject_input(),
            box_solid_fill(" ", 1),
            self._points_input(),
            box_solid_fill(" ", 1),
            self._status_input(),
            box_solid_fill(" ", 1),
            self._tags_input(),
            box_solid_fill(" ", 1),
            self._description_input(),
            box_solid_fill(" ", 1),
            self._requirements_input(),
            box_solid_fill(" ", 2),
            self._buttons(),
            box_solid_fill(" ", 1),
        ]
        self.widget = urwid.Pile(contents)

        title = "Edit User Story" if self.user_story else "Create User Story"
        super().__init__(urwid.Padding(urwid.LineBox(urwid.Padding(self.widget, right=2, left=2),
                                                     title), right=6, left=6))

    @property
    def subject(self):
        return self._subject_edit.get_edit_text()

    @property
    def points(self):
        return self._points

    @property
    def status(self):
        return self._status

    @property
    def tags(self):
        tags = self._tags_edit.get_edit_text()
        return tags.split(" ,") if tags else []

    @property
    def description(self):
        return self._description_edit.get_edit_text()

    @property
    def team_requirement(self):
        return self._team_requirement_checkbox.get_state()

    @property
    def client_requirement(self):
        return self._client_requirement_checkbox.get_state()

    def _subject_input(self):
        self._subject_edit = urwid.Edit(edit_text=self.user_story.get("subject", ""))

        colum_items = [(17, urwid.Padding(ListText("Subject", align="right"), right=4))]
        colum_items.append(urwid.AttrMap(self._subject_edit, "editor"))
        return urwid.Columns(colum_items)

    def _points_input(self):
        roles = data.computable_roles(self.project)
        points = data.points(self.project)
        max_length = max([len(s["name"]) for s in points.values()])

        self._role_points_groups = {}

        points_pile = []
        for r_id, role in roles.items():
            self._points[r_id] = (self.user_story.get("points", {}).get(r_id, None) or
                                  self.project.get("default_points", None))

            points_colum = [(17, urwid.Text(role["name"]))]
            points_group = []
            for p_id, point in points.items():
                urwid.RadioButton(points_group, point["name"],
                                  state=(int(p_id) == self.user_story.get("points", {}).get(r_id, None) or
                                         int(p_id) == self.project.get("default_points", None)),
                                  on_state_change=self._handler_point_radiobutton_change,
                                  user_data={r_id:point["id"]})

            points_colum.append(Grid(points_group, 4 + max_length, 2, 0, "left"))
            points_pile.append(urwid.Columns(points_colum))

            self._role_points_groups[r_id] = points_group

        self._points_checkbox = urwid.Pile(points_pile)

        colum_items = [(17, urwid.Padding(ListText("Points", align="right"), right=4))]
        colum_items.append(self._points_checkbox)
        return urwid.Columns(colum_items)

    def _handler_point_radiobutton_change(self, radio_button, new_state, user_data):
        if new_state:
            self._points.update(user_data)

    def _status_input(self):
        self._status = self.user_story.get("status", None) or self.project.get("default_us_status", None)

        us_statuses = data.us_statuses(self.project)
        max_length = max([len(s["name"]) for s in us_statuses.values()])

        self._us_status_group = []
        for s_id, status in us_statuses.items():
            urwid.RadioButton(self._us_status_group, status["name"],
                              state=(status["id"] == self.user_story.get("status", None) or
                                     status["id"] == self.project.get("default_us_status", None)),
                              on_state_change=self._handler_status_radiobutton_change,
                              user_data=status["id"])

        colum_items = [(17, urwid.Padding(ListText("Status", align="right"), right=4))]
        colum_items.append(Grid(self._us_status_group, 4 + max_length, 3, 0, "left"))
        return urwid.Columns(colum_items)

    def _handler_status_radiobutton_change(self, radio_button, new_state, user_data):
        if new_state:
            self._status = user_data

    def _tags_input(self):
        self._tags_edit = urwid.Edit(edit_text=", ".join(self.user_story.get("tags", [])))

        colum_items = [(17, urwid.Padding(ListText("Tags", align="right"), right=4))]
        colum_items.append(urwid.AttrMap(self._tags_edit, "editor"))
        return urwid.Columns(colum_items)

    def _description_input(self):
        self._description_edit = urwid.Edit(multiline=True, edit_text=self.user_story.get("subject", ""))

        colum_items = [(17, urwid.Padding(ListText("Description", align="right"), right=4))]
        colum_items.append(urwid.AttrMap(self._description_edit, "editor"))
        return urwid.Columns(colum_items)

    def _requirements_input(self):
        self._client_requirement_checkbox = urwid.CheckBox("Client's requirement",
                state=self.user_story.get("client_requirement", False))
        self._team_requirement_checkbox = urwid.CheckBox("Team's requirement",
                state=self.user_story.get("team_requirement", False))

        colum_items = [(17, urwid.Text(" "))]
        colum_items.append(self._client_requirement_checkbox)
        colum_items.append(self._team_requirement_checkbox)
        return urwid.Columns(colum_items)

    def _buttons(self):
        self.save_button = PlainButton("Save")
        self.cancel_button = PlainButton("Cancel")

        colum_items = [("weight", 1, urwid.Text(""))]
        colum_items.append((15, urwid.AttrMap(urwid.Padding(self.save_button, right=2, left=2),
                                              "submit-button") ))
        colum_items.append((2, urwid.Text(" ")))
        colum_items.append((15, urwid.AttrMap(urwid.Padding(self.cancel_button, right=1, left=2),
                                              "cancel-button") ))
        return urwid.Columns(colum_items)


# Issues

class ProjectIssuesStats(urwid.WidgetWrap):
    def __init__(self, project):
        self.project = project
        widget = urwid.Columns([
            ("weight", 0.25, urwid.Pile([urwid.Text("")])),
            ("weight", 0.25, urwid.Pile([urwid.Text("")])),
            ("weight", 0.25, urwid.Pile([urwid.Text("")])),
            ("weight", 0.25, urwid.Pile([urwid.Text("")])),
        ])
        super().__init__(widget)

    def populate(self, issues_stats):
        issues_statuses_stats = [urwid.Text(("cyan", "Per Status")),]
        issues_statuses_stats += [IssuesStatusStat(**ists) for ists in
                                  data.issues_statuses_stats(issues_stats).values()]
        issues_priorities_stats = [urwid.Text(("cyan", "Per Priority")),]
        issues_priorities_stats += [IssuesPriorityStat(**iprs) for iprs in
                                    data.issues_priorities_stats(issues_stats).values()]
        issues_severities_stats = [urwid.Text(("cyan", "Per Severity")),]
        issues_severities_stats += [IssuesSeverityStat(**ises) for ises in
                                    data.issues_severities_stats(issues_stats).values()]

        self._w = urwid.Columns([
            ("weight", 0.25, urwid.Pile([urwid.Text(""),
                TotalIssues(issues_stats), OpenedIssues(issues_stats), ClosedIssues(issues_stats)])),
            ("weight", 0.25, urwid.Pile(issues_statuses_stats)),
            ("weight", 0.25, urwid.Pile(issues_priorities_stats)),
            ("weight", 0.25, urwid.Pile(issues_severities_stats)),
        ])


class TotalIssues(urwid.Text):
    def __init__(self, issues_stats):
        text = ["Total issues: ", ("cyan", str(data.total_issues(issues_stats)))]
        super().__init__(text)


class OpenedIssues(urwid.Text):
    def __init__(self, issues_stats):
        text = ["Opened issues: ", ("red", str(data.opened_issues(issues_stats)))]
        super().__init__(text)


class ClosedIssues(urwid.Text):
    def __init__(self, issues_stats):
        text = ["Closed issues: ", ("green", str(data.closed_issues(issues_stats)))]
        super().__init__(text)


class IssuesStatusStat(urwid.Text):
    def __init__(self, name="", color="", count="", **kwargs):
        text = ["{}: ".format(name), (color, str(count))]
        super().__init__(text)


class IssuesPriorityStat(urwid.Text):
    def __init__(self, name="", color="", count="", **kwargs):
        text = ["{}: ".format(name), (color, str(count))]
        super().__init__(text)


class IssuesSeverityStat(urwid.Text):
    def __init__(self, name="", color="", count="", **kwargs):
        text = ["{}: ".format(name), (color, str(count))]
        super().__init__(text)


class IssuesList(mixins.ViMotionMixin, mixins.EmacsMotionMixin, urwid.WidgetWrap):
    def __init__(self, project):
        self.project = project

        self.header = IssuesListHeader()

        self.widget = urwid.Pile([self.header])
        super().__init__(self.widget)

    def populate(self, issues):
        if issues:
            self.reset()

        first_gains_focus = len(self.widget.contents) == 1 and issues

        for issue in issues:
            self.widget.contents.append((IssueEntry(issue, self.project),
                                         ("weight", 0.1)))

        if first_gains_focus:
            self.widget.contents.focus = 1

    def reset(self):
        self.widget.contents = self.widget.contents[:1]


class IssuesListHeader(urwid.WidgetWrap):
    def __init__(self):
        self.issue_button = PlainButton("Issue")
        self.status_button = PlainButton("Status")
        self.priority_button = PlainButton("Priority")
        self.severity_buttton = PlainButton("Severity")
        self.assigned_to_button = PlainButton("Assigned to")

        colum_items = [("weight", 0.55, ButtonCell(self.issue_button))]
        colum_items.append(("weight", 0.1, ButtonCell(self.status_button)))
        colum_items.append(("weight", 0.1, ButtonCell(self.priority_button)))
        colum_items.append(("weight", 0.1, ButtonCell(self.severity_buttton)))
        colum_items.append(("weight", 0.15, ButtonCell(self.assigned_to_button)))

        self.widget = urwid.Columns(colum_items)
        super().__init__(self.widget)


class IssueEntry(urwid.WidgetWrap):
    def __init__(self, issue, project):
        issue_ref_and_name = "#{0: <4} {1}".format(str(data.issue_ref(issue)), data.issue_subject(issue))

        colum_items = [("weight", 0.55, ListText(issue_ref_and_name, align="left"))]

        hex_color, status = data.issue_status_with_color(issue, project)
        color = color_to_hex(hex_color)
        attr = urwid.AttrSpec("h{0}".format(color), "default")
        colum_items.append(("weight", 0.1, ListText((attr, status))))

        hex_color, priority = data.issue_priority_with_color(issue, project)
        color = color_to_hex(hex_color)
        attr = urwid.AttrSpec("h{0}".format(color), "default")
        colum_items.append(("weight", 0.1, ListText((attr, priority))))

        hex_color, severity = data.issue_severity_with_color(issue, project)
        color = color_to_hex(hex_color)
        attr = urwid.AttrSpec("h{0}".format(color), "default")
        colum_items.append(("weight", 0.1, ListText((attr, severity))))

        hex_color, username =  data.issue_assigned_to_with_color(issue, project)
        color = color_to_hex(hex_color)
        attr = urwid.AttrSpec("h{0}".format(color), "default")
        colum_items.append(("weight", 0.15, ListText((attr, username))))

        self.widget = urwid.Columns(colum_items)
        super().__init__(urwid.AttrMap(self.widget, "default", "focus"))

    def selectable(self):
        return True



# Sprints

class ProjectSprintsStats(urwid.WidgetWrap):
    def __init__(self, project):
        self.project = project
        self.widget = urwid.Columns([ ])
        super().__init__(self.widget)

    def populate(self, milestone_stats):
        completed_points = sum(milestone_stats["completed_points"])
        total_points = sum(milestone_stats["total_points"].values())
        rem_points = total_points - completed_points
        completed_tasks = milestone_stats["completed_tasks"]
        total_tasks = milestone_stats["total_tasks"]
        rem_tasks = total_tasks - completed_tasks
        init_date = milestone_stats["estimated_start"]
        finish_date = milestone_stats["estimated_finish"]

        self._w = urwid.Columns([
            ("weight", 0.2, urwid.LineBox(urwid.Pile([ListText(""),
                    urwid.ProgressBar("progressbar-normal", "progressbar-complete", completed_points,
                                      total_points, "progressbar-smooth")]), "Status")),
            ("weight", 0.3, urwid.LineBox(Stack_1_3_1([total_points, completed_points, rem_points]), "Points")),
            ("weight", 0.3, urwid.LineBox(Stack_1_3_1( [total_tasks, completed_tasks, rem_tasks]), "Tasks")),
            ("weight", 0.3, urwid.LineBox(Color_dates(init_date, finish_date), "Dates")),
         ])

class ProjectSprintsUserStories(urwid.WidgetWrap):
    def __init__(self, project):
        self.project = project
        self.roles = data.computable_roles(project)
        self.widget = urwid.Pile([ListText("Fetching data")])
        super().__init__(self.widget)

    def populate(self, user_stories, milestone_tasks):
        if user_stories:
            self.reset()

        #import ipdb; ipdb.set_trace()
        for us in user_stories:
            points_by_role = data.us_points_by_role(us, self.project, self.roles.values())
            self.widget.contents.append((USTitleCell(us, self.roles.values(), points_by_role),
                                    ("weight", 0.1)))
            us_tasks = [t for t in milestone_tasks if t["user_story"] == us["id"]]
            for us_t in us_tasks:
                hex_color, username =  data.task_assigned_to_with_color(us_t, self.project)
                hex_status_color, status = data.task_status_with_color(us_t, self.project)
                text = self.HexToText(hex_color, username)
                text_status = self.HexToText(hex_status_color, status)
                self.widget.contents.append((UserStoryTask(us_t, text, text_status), ("weight", 0.1)))

        us_unassig = [t for t in milestone_tasks if t["user_story"] == None]
        if us_unassig:
            self.widget.contents.append((urwid.AttrMap(urwid.LineBox(urwid.AttrMap(ListText("Unassigned tasks"),
                "cyan", "focus-header")), "green"), ("weight", 0.1)))
            for una in us_unassig:
                self.widget.contents.append((UserStoryTask(una, text, text_status), ("weight", 0.1)))

        if len(self.widget.contents):
            self.widget.contents.focus = 0

    def reset(self):
        self.widget.contents = []

    def HexToText(self, hex_color, text):
        color = color_to_hex(hex_color)
        attr = urwid.AttrSpec("h{0}".format(color), "default")
        return ("weight", 0.2, ListText((attr, text)))


class USTitleCell(urwid.WidgetWrap):
    def __init__(self, us, roles, values):
        is_closed = urwid.AttrMap(ListText("☑"), "green", "focus-header") if us.get("is_closed", False) else urwid.AttrMap(ListText("☒"), "red", "focus-header")
        columns = [("weight", 0.05, is_closed)]

        left_description = urwid.Text("US #{0: <4} {1}".format(str(us["id"]), us["subject"]))
        columns.append(("weight", 0.8, left_description))

        for i, role in enumerate(roles):
            columns.append(("weight", 0.1, ListText("%s: %s" % (role["name"], values[i]))))

        columns.append(("weight", 0.1, ListText("TOTAL: {}".format(us["total_points"]))))
        widget = urwid.AttrMap(urwid.LineBox(urwid.AttrMap(urwid.Columns(columns), "cyan", "focus-header")), "green")
        super().__init__(urwid.AttrMap(widget, "default", "focus"))

    def selectable(self):
        return True

class UserStoryTask(urwid.WidgetWrap):
    def __init__(self, us_task, text, text_status):
        is_closed = urwid.AttrMap(ListText("☑"), "green", "focus") if us_task.get("finished_date", None) else urwid.AttrMap(ListText("☒"), "red", "focus")

        widget = urwid.Columns([
                ("weight", 0.05, is_closed),
                ("weight", 1, ListText("Task #{0: <4} {1}".format(str(us_task["ref"]), us_task["subject"]), align="left")),
                text,
                text_status,
                ])
        super().__init__(urwid.AttrMap(widget, "default", "focus"))

    def selectable(self):
        return True

# Wiki

class WikiPage(urwid.WidgetWrap):
    def __init__(self, project):
        self.project = project

        self.widget = urwid.Pile([ListText("No page found")])
        super().__init__(self.widget)

    def populate(self, wiki_page):
        self.slug_widget = ListText(data.slug(wiki_page))
        self.content_widget = urwid.Edit(edit_text=data.content(wiki_page), multiline=True, wrap='any',
                                     allow_tab=True)
        self.widget.contents = [
            (RowDivider(div_char=" "), ("weight", 0.1)),
            (self.slug_widget, ('weight', 1)),
            (RowDivider(div_char=" "), ("weight", 0.1)),
            (self.content_widget, ('pack', None)),
            (RowDivider(div_char=" "), ("weight", 0.1)),
            (urwid.Padding(self._buttons(), right=2, left=2), ('weight', 1)),
            (RowDivider(div_char=" "), ("weight", 0.1))
        ]
        self.widget.contents.focus = 3

    def _buttons(self):
        self.save_button = PlainButton("Save")
        self.reset_button = PlainButton("Reset")

        colum_items = [("weight", 1, urwid.Text(""))]
        colum_items.append((15, urwid.AttrMap(urwid.Padding(self.save_button, right=2, left=2),
                                              "submit-button") ))
        colum_items.append((2, urwid.Text(" ")))
        colum_items.append((15, urwid.AttrMap(urwid.Padding(self.reset_button, right=1, left=2),
                                              "cancel-button") ))
        return urwid.Columns(colum_items)

# Misc

class ListCell(urwid.WidgetWrap):
    def __init__(self, text):
        text_widget = urwid.AttrMap(ListText(text), "default")
        widget = urwid.AttrMap(urwid.LineBox(text_widget), "green")
        super().__init__(widget)


class ButtonCell(urwid.WidgetWrap):
    def __init__(self, button):
        text_widget = urwid.AttrMap(button, "default", "focus-header")
        widget = urwid.AttrMap(urwid.LineBox(text_widget), "green")
        super().__init__(widget)


class ListText(mixins.IgnoreKeyPressMixin, urwid.Text):
    def __init__(self, text, align="center"):
        super().__init__(text, align=align)


class RowDivider(urwid.WidgetWrap):
    def __init__(self, attr_map="default", div_char="-"):
        widget = urwid.AttrMap(urwid.Divider(div_char), attr_map)
        super().__init__(widget)

def color_to_hex(color):
    """
    Given either an hexadecimal or HTML color name, return a the hex
    approximation without the `#`.
    """
    if color.startswith("#"):
        return x256.from_hex(color.strip("#"))
    else:
        return x256.from_html_name(color)

class Color_text(ListText):
    def __init__(self, color, text):
        text = [(color, text)]
        super().__init__(text)

class Stack_1_3_1(urwid.Pile):
    def __init__(self, values):
        titles = ["Total", "Completed", "Remaining"]
        columns = []
        for i, name in enumerate(titles):
            columns.append(("weight", 0.33, urwid.Pile([ListText(name), Color_by_value(values[i], values[0])])))
        pile = [urwid.Columns(columns)]
        super().__init__(pile)

class Color_by_value(ListText):
    # TODO: Improve me
    def __init__(self, value, max_value=100.0):
        color = "yellow"
        if int(value) < int(max_value) * 0.2:
            color = "red"
        elif int(value) == int(max_value):
            color = "green"
        text = [(color, str(value))]
        super().__init__(text)

class Color_dates(urwid.Pile):
    def __init__(self, init_date, finish_date):
        dates_col = [
            urwid.Pile([ListText("Start"), Color_text("green", init_date)]),
            urwid.Pile([ListText("Finish"), Color_text("red", finish_date)])
        ]
        dates = [urwid.Columns(dates_col)]
        super().__init__(dates)