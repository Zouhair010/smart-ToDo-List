import sqlite3
from kivymd.app import MDApp
from kivymd.uix.pickers import MDDatePicker
from kivymd.uix.button import MDRaisedButton
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.gridlayout import MDGridLayout
from kivymd.uix.textfield import MDTextField
from kivy.uix.textinput import TextInput
from kivymd.uix.label import MDLabel
from kivymd.uix.dialog import MDDialog
from kivymd.uix.list import OneLineListItem, MDList, TwoLineListItem
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.widget import Widget
from kivymd.toast import toast
from kivymd.uix.button import MDRectangleFlatIconButton
from kivymd.uix.selectioncontrol import MDSwitch
from threading import Thread
# from kivy.utils import get_color_from_hex
from kivymd.color_definitions import colors
from kivy.clock import Clock
import time
from datetime import datetime, date

class FirstScreen(MDBoxLayout):
    def __init__(self, switch_callback, **kwargs):
        super().__init__(**kwargs)

        #the orientation and padding between items on the FirstScreen box layout
        self.orientation = "vertical"
        self.padding = 20
        self.spacing = 10

        #connect with the database
        self.mydb = sqlite3.connect('todo_list.db')
        self.my_cursor = self.mydb.cursor()
        self.my_cursor.execute(
            "CREATE TABLE IF NOT EXISTS todo_table (Id INTEGER PRIMARY KEY AUTOINCREMENT, Task TEXT NOT NULL, Date_exicution DATE NOT NULL)"
        )
        self.my_cursor.execute(
            "CREATE TABLE IF NOT EXISTS counter (Tasks_count INTEGER, curr_date DATE)"
        )
        self.my_cursor.execute(
            "CREATE TABLE IF NOT EXISTS mode (dark_mode INTEGER)"
        )
        self.mydb.commit()
        #the box layout that contains the the switch button and the label of dark mode
        self.darkModeLayout=MDBoxLayout(
            orientation = "horizontal",
            size_hint_y=None,
            height=50,
            spacing = 40
        )
        #switch button to change the theme of the app to the dark mode
        self.switchDark=MDSwitch()
        self.switchDark.bind(active=self.toggle_theme_style)
        self.darkModeLayout.add_widget(self.switchDark)
        self.darkModeLayout.add_widget(MDLabel(text="[u][i]Dark Mode[/i][/u]",markup=True))
        self.add_widget(self.darkModeLayout)

        #box layout that contains the current date and time on the top of the FirstScreen
        self.datetime_percent_boxlayout=MDBoxLayout(
            orientation = "horizontal",
            size_hint_y=None,
            height=40,
        )
        #the textinput that show the current date and time
        self.todays_date_time = TextInput(
            halign="center",#to make the current date and time appear on the center of the textinput
            readonly=True,
            size_hint=(None,None),
            font_size=20,
            size=(200,40),
            background_normal='',
            background_active='',
            background_color=(0,0,0,0)
        )
        #to make the current date and time appear on the left and
        # the percent on the right of the box layout horizontally:
        self.datetime_percent_boxlayout.add_widget(self.todays_date_time)
        self.datetime_percent_boxlayout.add_widget(Widget(height=100))# spacer
        #the textinput that show the percent of none complete tasks
        self.percent_textiput = TextInput(
            halign="center",#to make the percent appear on the center of the textinput
            readonly=True,
            size_hint=(None,None),
            font_size=20,
            size=(370,40),
            background_normal='',
            background_active='',
            background_color=(0,0,0,0)
        )
        self.datetime_percent_boxlayout.add_widget(self.percent_textiput)
        self.add_widget(self.datetime_percent_boxlayout)

        #the gridlayout that contains the tasks textfield and the add task button
        self.add_tasks_gridlayout = MDGridLayout(cols=2, spacing=10, padding=10, size_hint_y=None, height=100)
        #the textfield to enter a task
        self.task = MDTextField(hint_text="enter a task", mode="rectangle")
        self.add_tasks_gridlayout.add_widget(self.task)

        # the add button to append a task to the database
        # self.add_tasks_button = MDRaisedButton(
        #     text="add",
        #     # theme_text_color="Custom",
        #     font_style='H6'
        #     )
        
        self.add_tasks_button = MDRectangleFlatIconButton(
            text="  add",
            font_style='H6',
            icon="/home/itsme/Desktop/kivyMD_todolist/add_77928(1).ico",
            pos_hint={"center_x": 0.5, "center_y": 0.5}
        )
        self.add_tasks_button.bind(on_release=self.add_task) #call a fuction whene the add button clicked
        self.add_tasks_gridlayout.add_widget(self.add_tasks_button)
        self.add_widget(self.add_tasks_gridlayout)

        # the space between the add tasks boxlayout and the tasks list
        self.spacer = MDBoxLayout(size_hint_y=None, height=30,orientation ="horizontal",spacing=10, padding=10)
        self.todays_labal = MDLabel(
            text="[size=30][b][u]todays tasks[/u][/b][/size]",
            markup=True,
            theme_text_color="Custom",
            halign= "center",
            text_color=colors["Purple"]["400"]
        )
        self.spacer.add_widget(self.todays_labal)
        self.add_widget(self.spacer)

        #show the tasks list 
        self.scroll = MDScrollView()#to make tasks scroll
        self.task_list = MDList()
        self.scroll.add_widget(self.task_list)
        self.add_widget(self.scroll)

        #
        self.futur_tasks_boxlayout = MDBoxLayout(size_hint_y=None, height=30,orientation ="horizontal")
        self.futur_tasks_button = MDRaisedButton(
            text="future tasks",
            # theme_text_color="Custom",
            # font_style='H6'
        )
        self.futur_tasks_button.bind(on_release=switch_callback)
        self.futur_tasks_boxlayout.add_widget(Widget())
        self.futur_tasks_boxlayout.add_widget(self.futur_tasks_button)
        self.add_widget(self.futur_tasks_boxlayout)
        
        #a thread to make remainder work while the app work
        thread = Thread(target=self.remainder)
        thread.daemon = True
        thread.start()

        #a thread to show the current date and time while the app work
        thread1 = Thread(target=self.show_todays_date_time)
        thread1.daemon = True
        thread1.start()

        #delete the past tasks
        self.delete_past_tasks()

        #to load tasks on the tasks list
        self.load_tasks()

        #show the percent of none finished tasks
        self.percent_none_finished_tasks()

        self.last_theme_style()
    
    def last_theme_style(self):
        self.my_cursor.execute("SELECT dark_mode FROM mode;")
        row = self.my_cursor.fetchall()        
        if len(row) > 0:
            dark_mode = row[0][0]
            if dark_mode == 1:
                MDApp.get_running_app().theme_cls.theme_style = "Dark"
                self.switchDark.active=True
            else:
                MDApp.get_running_app().theme_cls.theme_style = "Light"
                self.switchDark.active=False

    #a function that change the theme of the app (dark,light) themes
    def toggle_theme_style(self, switch_instance, value):
        if value:
            MDApp.get_running_app().theme_cls.theme_style = "Dark"
            self.my_cursor.execute("DELETE FROM mode;")
            self.my_cursor.execute("INSERT INTO mode (dark_mode) VALUES (1);")
            self.mydb.commit()
        else:
            MDApp.get_running_app().theme_cls.theme_style = "Light"
            self.my_cursor.execute("DELETE FROM mode;")
            self.my_cursor.execute("INSERT INTO mode (dark_mode) VALUES (0);")
            self.mydb.commit()

    #a function that delete the past tasks
    def delete_past_tasks(self):
        self.my_cursor.execute("DELETE FROM todo_table WHERE Date_exicution < DATE('now');")
        self.mydb.commit()
        self.sort_tasks_by_date()

    #a function that count todays tasks
    def tasks_counter(self,date_):
        if date_ == str(date.today()):
            self.my_cursor.execute("SELECT Tasks_count FROM counter WHERE curr_date = DATE('now');")
            row = self.my_cursor.fetchall()        
            if len(row) > 0:
                tasks_cout = row[0][0]+1
                self.my_cursor.execute("DELETE FROM counter;")
                self.my_cursor.execute("INSERT INTO counter (Tasks_count, curr_date) VALUES (?,?);",(tasks_cout,str(date.today())))
                self.mydb.commit()
            else:
                self.my_cursor.execute("INSERT INTO counter (Tasks_count, curr_date) VALUES (?,?);",(1,str(date.today())))
                self.mydb.commit()

    #a function that calcule the percent of none finished tasks
    def percent_none_finished_tasks(self):
        self.my_cursor.execute("SELECT Tasks_count FROM counter WHERE curr_date = DATE('now');")
        row = self.my_cursor.fetchall()
        if len(row) > 0:
            total_tasks = row[0][0]
            self.my_cursor.execute("SELECT COUNT(Task) FROM todo_table where Date_exicution = DATE('now');")
            result = self.my_cursor.fetchall()
            if len(result) > 0:
                infinished_tasks = result[0][0]
                percent = (infinished_tasks/total_tasks)*100
                # print(percent)
                if percent != 0.0:
                    self.percent_textiput.text = f"{str(percent)[:4]}% of tasks not completed for today"
                    self.percent_textiput.foreground_color=colors["Blue"]["900"]
                else:
                    self.percent_textiput.text = f"{100}% of tasks completed for today"
                    self.percent_textiput.foreground_color=colors["Green"]["500"]
        else:
            self.percent_textiput.text = f"{100}% of tasks completed for today"
            self.percent_textiput.foreground_color=colors["Green"]["500"]

    #method to replace the current text(date and time) on the textinput(that show the date time) by the current date and time
    def replace_text_datetime_textfeild(self,today):
        self.todays_date_time.text=today
        self.todays_date_time.foreground_color=colors["Blue"]["900"]
    
    #method that show and refrish todays date and time 
    def show_todays_date_time(self):
        while True:
            todays_date_time = datetime.now().replace(microsecond=0)
            Clock.schedule_once(lambda dt: self.replace_text_datetime_textfeild(str(todays_date_time)))
            # print(todays_date_time)
            time.sleep(1)
    
    #method that work whene add button clicked 
    def add_task(self, instance):
        if self.task.text.strip() == "":
            toast("the task entry is empty! you should enter a task",duration=4) #if the textfeild that should contains a task is empty
            return
        date_picker = MDDatePicker()
        date_picker.bind(on_save=self.on_date_selected) #whene tha date is selected
        date_picker.open() #raise a calander to packe date
    
    #method that insert the task and the selected date into the database whene the date is selected
    def on_date_selected(self, instance, value, date_range):
        task_text = self.task.text.strip()
        formatted_date = str(value)
        sql = "INSERT INTO todo_table (Task, Date_exicution) VALUES (?, ?)"
        self.my_cursor.execute(sql, (task_text, formatted_date))
        self.mydb.commit()
        self.tasks_counter(formatted_date)
        self.task.text = ""
        self.sort_tasks_by_date() #sort tasks by date on the database
        self.load_tasks() #reload tasks on the tasks list
        self.percent_none_finished_tasks()

    #method that remove the selected task in the tasks list from the database
    def on_select_finish_task(self, task_id, task):
        self.my_cursor.execute("DELETE FROM todo_table WHERE Id = ?", (task_id,))
        self.mydb.commit()
        self.percent_none_finished_tasks()
        self.sort_tasks_by_date() #sort tasks by date after finishing and removing a specific task
        self.load_tasks() #reload tasks on the tasks list
        self.show_dialog(f'great you finish "{task}"') #raise a dialog tells that you finish a specific task
    
    #method that sort tasks by date
    def sort_tasks_by_date(self):
        self.my_cursor.execute('select Task,Date_exicution from todo_table ORDER BY Date_exicution')#select tasks from the table sorted by date
        myresult = self.my_cursor.fetchall() #the tasks from the database
        self.my_cursor.execute('delete from todo_table') #delete all tasks from the table
        self.my_cursor.execute("DELETE FROM sqlite_sequence WHERE name='todo_table'") #make the auto increment start from (1)
        for data in myresult:
            self.my_cursor.execute('insert into todo_table (Task,Date_exicution) values (?,?)', (data[0],data[1])) #insert the sorted tasks
        self.mydb.commit()

    #a function that load data on a mdlist
    def load_tasks(self):
        self.task_list.clear_widgets()
        self.my_cursor.execute("SELECT Id, Task, Date_exicution FROM todo_table WHERE Date_exicution = DATE('now');")
        rows = self.my_cursor.fetchall()
        for task_id, task, date in rows:
            item_text = f"[u]{task_id}:   {task} [/u]"
            self.task_list.add_widget(TwoLineListItem(
                text=item_text,
                font_style='H6',
                secondary_text= f"{date}",
                theme_text_color="Custom",
                # text_color= get_color_from_hex("#9933ff"),
                text_color= colors["Blue"]["800"],
                secondary_theme_text_color="Custom",
                # secondary_text_color= get_color_from_hex("#9933ff"),
                secondary_text_color= colors["Green"]["400"],
                on_release=lambda x, task_id=task_id, task=task: self.on_select_finish_task(task_id,task)
            ))
    
    #a dialog to show a specific text or message
    def show_dialog(self, message):
        dialog = MDDialog(
            title="info",
            text=message,
            size_hint=(0.8, 0.3),
            # buttons=[]
        )
        dialog.open()

    #a function that remaind for the next task
    def remainder(self):
        s,m = 0,0
        while True:
            time.sleep(1)
            s+=1
            if s%60==0:
                s=0
                m+=1
                if m%60==0:
                    m=0
                    mydb = sqlite3.connect('todo_list.db')
                    my_cursor = mydb.cursor()
                    my_cursor.execute("SELECT Task FROM todo_table WHERE Id=1 AND Date_exicution = DATE('now');")
                    rows = my_cursor.fetchall()
                    message = "No next task for today"
                    if len(rows)>0:
                        message = f'remember your next task is "{rows[0][0]}"'
                    my_cursor.close()
                    mydb.close()

                    Clock.schedule_once(lambda dt: toast(message,duration=6))

class SecondScreen(MDBoxLayout):
    def __init__(self, switch_callback, **kwargs):
        super().__init__(**kwargs)

        #connect with the database
        self.mydb = sqlite3.connect('todo_list.db')
        self.my_cursor = self.mydb.cursor()

        self.tasks_boxlayout = MDBoxLayout(orientation = "vertical")

        self.upper_boxlayout = MDBoxLayout(size_hint_y=None, height=50,padding= 7,orientation ="horizontal")

        self.upper_boxlayout.add_widget(Widget())
        self.goback_button = MDRaisedButton(
            text="back",
        )
        self.goback_button.bind(on_release=switch_callback)
        self.upper_boxlayout.add_widget(self.goback_button)
        self.tasks_boxlayout.add_widget(self.upper_boxlayout)

        #show the tasks list 
        self.scroll = MDScrollView()#to make tasks scroll
        self.task_list = MDList()
        self.scroll.add_widget(self.task_list)
        self.tasks_boxlayout.add_widget(self.scroll)
        self.add_widget(self.tasks_boxlayout)
        
        self.load_tasks()

    def load_tasks(self):
        self.task_list.clear_widgets()
        self.my_cursor.execute("SELECT Id, Task, Date_exicution FROM todo_table WHERE Date_exicution > DATE('now');")
        rows = self.my_cursor.fetchall()
        for task_id, task, date in rows:
            item_text = f"[u]*/ {task} [/u]"
            self.task_list.add_widget(TwoLineListItem(
                text=item_text,
                font_style='H6',
                secondary_text= f"{date}",
                theme_text_color="Custom",
                # text_color= get_color_from_hex("#9933ff"),
                text_color= colors["Blue"]["800"],
                secondary_theme_text_color="Custom",
                # secondary_text_color= get_color_from_hex("#9933ff"),
                secondary_text_color= colors["Green"]["400"],
                on_release=lambda x, task_id=task_id, task=task: self.on_select_finish_task(task_id,task)
            ))

    #method that remove the selected task in the tasks list from the database
    def on_select_finish_task(self, task_id, task):
        self.my_cursor.execute("DELETE FROM todo_table WHERE Id = ?", (task_id,))
        self.mydb.commit()
        self.sort_tasks_by_date() #sort tasks by date after finishing and removing a specific task
        self.load_tasks() #reload tasks on the tasks list
        self.show_dialog(f'great you finish "{task}"') #raise a dialog tells that you finish a specific task

    #a dialog to show a specific text or message
    def show_dialog(self, message):
        dialog = MDDialog(
            title="info",
            text=message,
            size_hint=(0.8, 0.3),
        )
        dialog.open()

    #method that sort tasks by date
    def sort_tasks_by_date(self):
        self.my_cursor.execute('select Task,Date_exicution from todo_table ORDER BY Date_exicution')#select tasks from the table sorted by date
        myresult = self.my_cursor.fetchall() #the tasks from the database
        self.my_cursor.execute('delete from todo_table') #delete all tasks from the table
        self.my_cursor.execute("DELETE FROM sqlite_sequence WHERE name='todo_table'") #make the auto increment start from (1)
        for data in myresult:
            self.my_cursor.execute('insert into todo_table (Task,Date_exicution) values (?,?)', (data[0],data[1])) #insert the sorted tasks
        self.mydb.commit()

class TodoList(MDApp):
    def build(self):
        self.first_screen = FirstScreen(self.show_second_screen)
        self.second_screen = SecondScreen(self.show_first_screen)
        self.root_layout = MDBoxLayout()
        
        self.root_layout.add_widget(self.first_screen)
        return self.root_layout
    def show_first_screen(self,instance=None):
        self.root_layout.clear_widgets()
        self.root_layout.add_widget(self.first_screen)
    def show_second_screen(self,instance=None):
        self.root_layout.clear_widgets()
        self.second_screen.load_tasks()
        self.root_layout.add_widget(self.second_screen)


if __name__ == "__main__":
    TodoList().run()