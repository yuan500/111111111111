"""
FATE ENDS 系统算力分配程序 - 移动端 (Kivy)
=========================================
从 tkinter 桌面版移植到 Kivy 移动端框架。
兼容 Android / iOS，可用 Buildozer 打包为 APK。
"""

import os
import sys
import re
import json
import random
import socket
import threading
import time

# ======================== Kivy 初始化配置 ========================
from kivy.config import Config
Config.set('graphics', 'width', '420')
Config.set('graphics', 'height', '780')
Config.set('graphics', 'resizable', False)
Config.set('kivy', 'window_icon', 'icon.png')

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup
from kivy.uix.progressbar import ProgressBar
from kivy.uix.checkbox import CheckBox
from kivy.uix.switch import Switch
from kivy.uix.widget import Widget
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.stacklayout import StackLayout
from kivy.uix.image import Image
from kivy.graphics import Color, RoundedRectangle, Rectangle, Ellipse
from kivy.clock import Clock, mainthread
from kivy.core.window import Window
from kivy.lang import Builder
from kivy.properties import (
    StringProperty, NumericProperty, BooleanProperty,
    ObjectProperty, ListProperty, ColorProperty
)
from kivy.metrics import dp, sp
from kivy.utils import get_color_from_hex, platform
from kivy.animation import Animation

# ======================== 颜色定义 ========================
ACCENT = '#2563eb'
ACCENT_HOVER = '#1d4ed8'
ACCENT_PRESS = '#1e40af'
TEXT_PRIMARY = '#111827'
TEXT_SECONDARY = '#6b7280'
DANGER = '#ef4444'
DANGER_HOVER = '#dc2626'
SUCCESS = '#16a34a'
WARNING = '#f59e0b'
BG_PRIMARY = '#f8f9fa'
BG_CARD = '#ffffff'
BORDER = '#e5e7eb'
BG_SECONDARY = '#f3f4f6'


# ======================== 网络检测 ========================
def check_network(host="8.8.8.8", port=53, timeout=2):
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        sock.connect((host, port))
        sock.close()
        return True
    except (socket.error, OSError):
        return False


# ======================== 弹窗帮助 ========================
def show_popup(title, message, icon_color=ACCENT, icon_char='i',
               buttons=None, dismiss_callback=None):
    """通用弹窗"""
    if buttons is None:
        buttons = [('确定', True)]

    content = BoxLayout(orientation='vertical', padding=dp(24), spacing=dp(16),
                        size_hint_y=None)
    content.bind(minimum_height=content.setter('height'))

    # 图标
    icon_container = BoxLayout(orientation='horizontal',
                               size_hint_y=None, height=dp(64))
    icon_box = FloatLayout(size_hint=(None, None), size=(dp(60), dp(60)),
                           pos_hint={'center_x': .5})
    with icon_box.canvas:
        Color(*get_color_from_hex(icon_color))
        Ellipse(pos=(0, 0), size=(dp(60), dp(60)))
    icon_label = Label(text=icon_char,
                       font_size=sp(28),
                       color=get_color_from_hex('#ffffff'),
                       bold=True,
                       size_hint=(None, None),
                       size=(dp(60), dp(60)),
                       pos_hint={'center_x': .5, 'center_y': .5})
    icon_box.add_widget(icon_label)
    icon_container.add_widget(Widget(size_hint_x=1))
    icon_container.add_widget(icon_box)
    icon_container.add_widget(Widget(size_hint_x=1))
    content.add_widget(icon_container)

    # 消息
    msg_label = Label(text=message,
                      font_size=sp(16),
                      color=get_color_from_hex(TEXT_PRIMARY),
                      halign='center', valign='middle',
                      size_hint_y=None, height=dp(60))
    msg_label.bind(texture_size=msg_label.setter('size'))
    content.add_widget(msg_label)

    # 按钮
    btn_box = BoxLayout(orientation='horizontal',
                        spacing=dp(10), size_hint_y=None, height=dp(48))
    btn_box.add_widget(Widget(size_hint_x=1))

    for text, is_primary in reversed(buttons):
        btn = Button(
            text=text,
            font_size=sp(16),
            bold=is_primary,
            background_normal='',
            background_color=get_color_from_hex(
                ACCENT if is_primary else BG_SECONDARY),
            color=get_color_from_hex(
                '#ffffff' if is_primary else TEXT_PRIMARY),
            size_hint=(None, None),
            size=(dp(120), dp(48))
        )
        btn.bind(on_release=lambda *a, b=is_primary, d=dismiss_callback, p=popup:
                 (d and d(b), p.dismiss()))
        btn_box.add_widget(btn)

    btn_box.add_widget(Widget(size_hint_x=1))
    content.add_widget(btn_box)

    popup = Popup(title=title,
                  title_size=sp(18),
                  title_color=get_color_from_hex(TEXT_PRIMARY),
                  content=content,
                  size_hint=(0.85, None),
                  height=dp(260),
                  background='',
                  separator_color=get_color_from_hex(BORDER),
                  title_align='center',
                  auto_dismiss=False)
    return popup


def show_info_popup(title, message, callback=None):
    popup = show_popup(title, message, icon_color=ACCENT, icon_char='i',
                       dismiss_callback=lambda _: callback and callback())
    popup.open()
    return popup


def show_warning_popup(title, message, callback=None):
    popup = show_popup(title, message, icon_color=WARNING, icon_char='!',
                       dismiss_callback=lambda _: callback and callback())
    popup.open()
    return popup


def show_error_popup(title, message, callback=None):
    popup = show_popup(title, message, icon_color=DANGER, icon_char='✕',
                       dismiss_callback=lambda _: callback and callback())
    popup.open()
    return popup


def show_confirm_popup(title, message, ok_text='确定', cancel_text='取消',
                       on_ok=None, on_cancel=None):
    """确认弹窗，返回 True/False"""
    result = {'ok': False}

    def _on_dismiss(is_primary):
        if is_primary:
            result['ok'] = True
            on_ok and on_ok()
        else:
            on_cancel and on_cancel()

    popup = show_popup(title, message, icon_color=ACCENT, icon_char='?',
                       buttons=[(ok_text, True), (cancel_text, False)],
                       dismiss_callback=_on_dismiss)
    popup.open()
    return lambda: result['ok']


# ======================== 启动闪屏 ========================
class SplashScreen(BoxLayout):
    pass


# ======================== 地址卡片组件 ========================
class AddressCard(BoxLayout):
    """单个地址卡片 - 移动端优化"""
    TRC20_PATTERN = re.compile(r'^T[A-HJ-NP-Za-km-z1-9]{33}$')

    index = NumericProperty(0)
    address = StringProperty('')
    power = StringProperty('0.00')
    speed = StringProperty('0')
    is_locked = BooleanProperty(False)
    is_selected = BooleanProperty(False)
    locked_color = ColorProperty(get_color_from_hex(TEXT_SECONDARY))

    def __init__(self, index=0, default_power=0, **kwargs):
        super().__init__(**kwargs)
        self.index = index
        self.power = f'{default_power:.2f}'
        self.on_power_change_cb = None
        self.on_state_changed_cb = None
        self.on_delete_cb = None
        self.on_speed_visible_cb = None
        self._speed_visible = False
        self._updating_power = False

    def on_locked_color(self, instance, value):
        pass

    def get_power_value(self):
        try:
            return round(float(self.power), 2)
        except ValueError:
            return 0.0

    def validate_trc20(self, addr):
        return self.TRC20_PATTERN.match(addr) is not None

    def on_confirm(self):
        if self.is_locked:
            show_warning_popup('提示', '该地址已锁定，无法修改')
            return

        addr = self.address.strip()
        if not addr:
            show_warning_popup('输入错误', '请输入目标地址')
            return

        if not self.validate_trc20(addr):
            show_error_popup('格式错误',
                             'TRC-20 地址格式错误！\n必须以 T 开头、长度 34 位')
            return

        # 算力校验
        if self.on_power_change_cb:
            valid, msg = self.on_power_change_cb(check_only=True)
            if not valid:
                show_warning_popup('算力校验失败', msg)
                return

        self._show_progress()

    def _show_progress(self):
        delay = random.uniform(2, 5)
        total = [0]

        content = BoxLayout(orientation='vertical', padding=dp(24), spacing=dp(12))
        label = Label(text='正在修改目标地址，请稍后...',
                      font_size=sp(16), color=get_color_from_hex(TEXT_PRIMARY))
        progress = ProgressBar(max=100, value=0, size_hint_y=None, height=dp(6))
        content.add_widget(label)
        content.add_widget(progress)

        popup = Popup(title='正在修改目标地址',
                      title_size=sp(16),
                      content=content,
                      size_hint=(0.85, None),
                      height=dp(180),
                      background='',
                      auto_dismiss=False)
        popup.open()

        def update_progress(dt):
            total[0] += 1
            progress.value = total[0] * (100 / 100)
            if total[0] >= 100:
                return False

        def done(dt):
            popup.dismiss()
            show_confirm_popup('操作成功',
                               '目标地址已上传至服务器\n点击确认完成',
                               on_ok=self.lock_input)

        Clock.schedule_once(done, delay)
        Clock.schedule_interval(update_progress, delay / 100)

    def lock_input(self):
        self.is_locked = True
        self._speed_visible = False
        self.locked_color = get_color_from_hex(DANGER)

        # 延迟显示速度
        delay = random.uniform(1, 3)
        Clock.schedule_once(lambda dt: self._enable_speed_display(), delay)

        if self.on_state_changed_cb:
            self.on_state_changed_cb()

    def _enable_speed_display(self):
        self._speed_visible = True
        if self.on_speed_visible_cb:
            self.on_speed_visible_cb()

    def unlock_input(self):
        self.is_locked = False
        self._speed_visible = False
        self.locked_color = get_color_from_hex(TEXT_PRIMARY)
        if self.on_state_changed_cb:
            self.on_state_changed_cb()

    def on_cancel(self):
        if not self.address.strip() and not self.is_locked:
            show_info_popup('提示', '输入框为空，无需取消')
            return

        if self.is_locked:
            def on_ok():
                self.unlock_input()

            show_confirm_popup('取消锁定',
                               '该地址已锁定，是否取消锁定？',
                               ok_text='取消锁定',
                               on_ok=on_ok)
            return

        def on_ok():
            self._show_cancel_progress()

        show_confirm_popup('取消确认',
                           '是否取消关闭或更换目标地址？',
                           ok_text='确认取消',
                           on_ok=on_ok)

    def _show_cancel_progress(self):
        delay = random.uniform(2, 6)
        content = BoxLayout(orientation='vertical', padding=dp(24))
        Label(text='正在连接服务器...', font_size=sp(16),
              color=get_color_from_hex(TEXT_PRIMARY))
        content.add_widget(Label(text='正在连接服务器...',
                                 font_size=sp(16),
                                 color=get_color_from_hex(TEXT_PRIMARY)))

        popup = Popup(title='正在连接服务器',
                      title_size=sp(16),
                      content=content,
                      size_hint=(0.85, None),
                      height=dp(160),
                      background='',
                      auto_dismiss=False)
        popup.open()

        def done(dt):
            popup.dismiss()
            show_info_popup('操作完成', '取消成功！')
            self.address = ''
            self._updating_power = True
            self.power = '0.00'
            self._updating_power = False
            if self.on_power_change_cb:
                self.on_power_change_cb()

        Clock.schedule_once(done, delay)

    def on_delete_click(self):
        def on_ok():
            delay = random.uniform(2, 6)

            content = BoxLayout(orientation='vertical', padding=dp(24))
            content.add_widget(Label(text='正在连接服务器删除地址...',
                                     font_size=sp(16),
                                     color=get_color_from_hex(TEXT_PRIMARY)))

            popup = Popup(title='正在删除',
                          title_size=sp(16),
                          content=content,
                          size_hint=(0.85, None),
                          height=dp(160),
                          background='',
                          auto_dismiss=False)
            popup.open()

            def done(dt):
                popup.dismiss()
                if self.on_delete_cb:
                    self.on_delete_cb(self.index)

            Clock.schedule_once(done, delay)

        show_confirm_popup('删除确认',
                           '是否确定删除此输入框？',
                           ok_text='确定删除',
                           on_ok=on_ok)

    def power_change(self, value):
        """算力滑块变化"""
        if self._updating_power or self.is_locked:
            return
        self.power = f'{value:.2f}'
        if self.on_power_change_cb:
            self.on_power_change_cb()

    def power_text_change(self, text):
        """算力文本输入变化"""
        if self._updating_power or self.is_locked:
            return
        # 只允许数字和小数点
        if text and not re.match(r'^\d{1,3}(\.\d{0,2})?$', text):
            return
        self.power = text if text else '0'
        if self.on_power_change_cb:
            self.on_power_change_cb()

    def set_speed(self, total_speed):
        """设置显示速度"""
        if not self.is_locked or not self._speed_visible:
            self.speed = '0'
            return
        power_val = self.get_power_value()
        speed_val = int(total_speed * power_val / 100)
        speed_val = int(speed_val * random.uniform(0.95, 1.05))
        self.speed = f'{speed_val:,}'


# ======================== 主界面 ========================
KV = '''
#:import hex kivy.utils.get_color_from_hex
#:import dp kivy.metrics.dp
#:import sp kivy.metrics.sp

<SplashScreen>:
    orientation: 'vertical'
    canvas.before:
        Color:
            rgba: hex('#fafafa')
        Rectangle:
            pos: self.pos
            size: self.size

    Widget:
        size_hint_y: 0.2

    FloatLayout:
        size_hint_y: None
        height: dp(70)
        canvas:
            Color:
                rgba: hex('#2563eb')
            Ellipse:
                pos: self.width/2 - dp(35), 0
                size: dp(70), dp(70)
        Label:
            text: 'FE'
            font_size: sp(32)
            bold: True
            color: hex('#ffffff')
            size_hint: None, None
            size: dp(70), dp(70)
            pos_hint: {'center_x': .5}

    Label:
        text: 'FATE ENDS 系统算力分配程序'
        font_size: sp(20)
        bold: True
        color: hex('#111827')
        size_hint_y: None
        height: dp(50)

    Label:
        id: splash_status
        text: '正在连接 38.65.91.10 服务器集群...'
        font_size: sp(14)
        color: hex('#6b7280')
        size_hint_y: None
        height: dp(36)

    ProgressBar:
        id: splash_progress
        max: 100
        value: 0
        size_hint_x: 0.7
        size_hint_y: None
        height: dp(4)
        pos_hint: {'center_x': .5}

    Label:
        id: splash_hint
        text: '预计剩余 0 秒'
        font_size: sp(14)
        color: hex('#6b7280')
        size_hint_y: None
        height: dp(30)

    Widget:
        size_hint_y: 0.2


<AddressCard>:
    orientation: 'vertical'
    size_hint_y: None
    height: dp(200) if root.is_locked else dp(220)
    padding: dp(10), dp(8)
    spacing: dp(6)

    canvas.before:
        Color:
            rgba: hex('#ffffff')
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [dp(12)]

    # 标题行
    BoxLayout:
        size_hint_y: None
        height: dp(32)
        orientation: 'horizontal'
        spacing: dp(8)

        CheckBox:
            id: card_checkbox
            size_hint: None, None
            size: dp(30), dp(30)
            active: root.is_selected
            on_active: root.is_selected = self.active
            disabled: root.is_locked

        Label:
            id: title_label
            text: f'目标地址 {root.index + 1:02d}'
            font_size: sp(16)
            bold: True
            color: root.locked_color
            size_hint_x: 1
            halign: 'left'
            valign: 'middle'
            text_size: self.size
            shorten: True

        Switch:
            size_hint: None, None
            size: dp(50), dp(30)
            active: root.is_locked
            disabled: True
            opacity: 0.6 if not root.is_locked else 1

    # 地址输入
    TextInput:
        id: address_input
        text: root.address
        on_text: root.address = self.text
        hint_text: '输入 TRC-20 目标地址'
        hint_text_color: hex('#9ca3af')
        font_size: sp(16)
        multiline: False
        size_hint_y: None
        height: dp(44)
        background_color: hex('#f3f4f6') if root.is_locked else hex('#ffffff')
        foreground_color: hex('#111827')
        disabled: root.is_locked
        cursor_color: hex('#2563eb')
        selection_color: hex('#bfdbfe')
        padding: [dp(10), dp(10)]

    # 算力 + 速度行
    BoxLayout:
        size_hint_y: None
        height: dp(44)
        orientation: 'horizontal'
        spacing: dp(6)

        # 算力滑块
        BoxLayout:
            size_hint_x: 0.55
            orientation: 'vertical'
            spacing: dp(2)

            BoxLayout:
                size_hint_y: None
                height: dp(20)
                orientation: 'horizontal'
                spacing: dp(4)

                Label:
                    text: '算力'
                    font_size: sp(12)
                    color: hex('#2563eb')
                    size_hint_x: None
                    width: dp(36)
                    halign: 'left'

                Label:
                    text: f'{root.power}％'
                    font_size: sp(12)
                    bold: True
                    color: hex('#111827')
                    size_hint_x: None
                    width: dp(72)
                    halign: 'right'

            Slider:
                id: power_slider
                min: 0
                max: 100
                value: float(root.power) if root.power else 0
                step: 0.1
                on_value: root.power_change(self.value) if not root.is_locked else None
                disabled: root.is_locked
                value_track: True
                value_track_color: hex('#2563eb')

        # 速度显示
        BoxLayout:
            size_hint_x: 0.25
            orientation: 'vertical'
            spacing: dp(2)

            Label:
                text: '速度'
                font_size: sp(11)
                color: hex('#9ca3af')
                size_hint_y: None
                height: dp(16)
                halign: 'center'

            Label:
                text: root.speed
                font_size: sp(16)
                bold: True
                color: hex('#111827') if root.is_locked else hex('#9ca3af')
                size_hint_y: None
                height: dp(24)
                halign: 'center'

        # 状态标记
        BoxLayout:
            size_hint_x: 0.2
            padding: [dp(4), 0]

            Label:
                text: '已锁定' if root.is_locked else '编辑中'
                font_size: sp(11)
                bold: True
                color: hex('#16a34a') if root.is_locked else hex('#6b7280')
                halign: 'center'
                valign: 'middle'

    # 操作按钮行
    BoxLayout:
        size_hint_y: None
        height: dp(40)
        orientation: 'horizontal'
        spacing: dp(6)

        Button:
            text: '确认'
            font_size: sp(14)
            bold: True
            background_normal: ''
            background_color: hex('#2563eb')
            color: hex('#ffffff')
            on_release: root.on_confirm()
            disabled: root.is_locked
            background_disabled_normal: ''
            disabled_color: hex('#9ca3af')

        Button:
            text: '取消'
            font_size: sp(14)
            background_normal: ''
            background_color: hex('#e5e7eb')
            color: hex('#111827')
            on_release: root.on_cancel()
            background_disabled_normal: ''
            disabled_color: hex('#9ca3af')

        Button:
            text: '删除'
            font_size: sp(14)
            bold: True
            background_normal: ''
            background_color: hex('#ef4444')
            color: hex('#ffffff')
            on_release: root.on_delete_click()


<MainScreen>:
    orientation: 'vertical'
    canvas.before:
        Color:
            rgba: hex('#f8f9fa')
        Rectangle:
            pos: self.pos
            size: self.size

    # 顶部栏
    BoxLayout:
        size_hint_y: None
        height: dp(56)
        padding: dp(10), dp(6)
        spacing: dp(10)
        canvas.before:
            Color:
                rgba: hex('#ffffff')
            Rectangle:
                pos: self.pos
                size: self.size

        Label:
            text: 'FATE ENDS 算力分配'
            font_size: sp(18)
            bold: True
            color: hex('#111827')
            size_hint_x: 0.45
            halign: 'left'
            valign: 'middle'

        Label:
            id: header_speed
            text: '0'
            font_size: sp(16)
            bold: True
            color: hex('#2563eb')
            size_hint_x: 0.35
            halign: 'right'
            valign: 'middle'
            shorten: True

    # 分隔线
    Widget:
        size_hint_y: None
        height: dp(1)
        canvas:
            Color:
                rgba: hex('#e5e7eb')
            Rectangle:
                pos: self.pos
                size: self.size

    # 可滚动卡片区域
    ScrollView:
        id: scroll_view
        do_scroll_x: False
        bar_width: dp(4)
        scroll_type: ['bars', 'content']

        GridLayout:
            id: card_container
            cols: 1
            spacing: dp(8)
            padding: dp(8), dp(8)
            size_hint_y: None
            height: self.minimum_height

    # 分隔线
    Widget:
        size_hint_y: None
        height: dp(1)
        canvas:
            Color:
                rgba: hex('#e5e7eb')
            Rectangle:
                pos: self.pos
                size: self.size

    # 底部操作栏
    BoxLayout:
        size_hint_y: None
        height: dp(100)
        padding: dp(6), dp(6)
        spacing: dp(4)
        canvas.before:
            Color:
                rgba: hex('#ffffff')
            Rectangle:
                pos: self.pos
                size: self.size

        GridLayout:
            cols: 3
            rows: 2
            spacing: dp(4)
            padding: dp(4), dp(2)

            Button:
                text: '全选'
                font_size: sp(13)
                background_normal: ''
                background_color: hex('#2563eb')
                color: hex('#ffffff')
                on_release: root.on_select_all()

            Button:
                text: '新增地址'
                font_size: sp(13)
                background_normal: ''
                background_color: hex('#16a34a')
                color: hex('#ffffff')
                on_release: root.add_address()

            Button:
                text: '导入地址'
                font_size: sp(13)
                background_normal: ''
                background_color: hex('#16a34a')
                color: hex('#ffffff')
                on_release: root.import_addresses()

            Button:
                text: '分配算力'
                font_size: sp(13)
                background_normal: ''
                background_color: hex('#f59e0b')
                color: hex('#ffffff')
                bold: True
                on_release: root.redistribute_power()

            Button:
                text: '批量确认'
                font_size: sp(13)
                bold: True
                background_normal: ''
                background_color: hex('#2563eb')
                color: hex('#ffffff')
                on_release: root.batch_confirm()

            Button:
                text: '批量取消'
                font_size: sp(13)
                background_normal: ''
                background_color: hex('#e5e7eb')
                color: hex('#111827')
                on_release: root.batch_cancel()

    # 状态栏
    BoxLayout:
        size_hint_y: None
        height: dp(36)
        padding: dp(10), 0
        canvas.before:
            Color:
                rgba: hex('#ffffff')
            Rectangle:
                pos: self.pos
                size: self.size

        Label:
            id: status_label
            text: '系统就绪 | 地址: 5 | 锁定: 0'
            font_size: sp(12)
            color: hex('#6b7280')
            size_hint_x: 0.65
            halign: 'left'
            valign: 'middle'

        Label:
            id: power_total_label
            text: '算力: 100％'
            font_size: sp(12)
            bold: True
            color: hex('#16a34a')
            size_hint_x: 0.35
            halign: 'right'
            valign: 'middle'
'''


class MainScreen(BoxLayout):
    """主界面 - 移动端版"""

    def __init__(self, app_ref, **kwargs):
        super().__init__(**kwargs)
        self.app = app_ref
        self.cards = []
        self.frame_count = 5
        self.current_speed = 0
        self.header_speed_running = False
        self._network_lost = False
        self._save_pending = False

        # 启动后初始化
        Clock.schedule_once(lambda dt: self._after_init(), 0.1)

    def _after_init(self):
        """初始化 UI 和加载配置"""
        self.card_container = self.ids.card_container
        self.status_label = self.ids.status_label
        self.power_total_label = self.ids.power_total_label
        self.scroll_view = self.ids.scroll_view

        # 创建默认卡片
        default_power = 100.0 / self.frame_count
        for i in range(self.frame_count):
            power = round(default_power, 2)
            self._create_card(i, power)

        self.update_status()
        self.validate_power_total()
        self.start_speed_animation()
        self.load_config()
        self._start_network_monitor()

    def _create_card(self, index, default_power=0):
        """创建一个地址卡片"""
        card = AddressCard(index=index, default_power=default_power)
        card.on_power_change_cb = self.validate_power_total
        card.on_state_changed_cb = self.save_config
        card.on_delete_cb = self.delete_card
        card.on_speed_visible_cb = self._on_card_speed_visible
        self.card_container.add_widget(card)
        self.cards.append(card)
        return card

    def _on_card_speed_visible(self):
        """某卡片速度显示就绪后，延迟启动头部速度"""
        if self.header_speed_running:
            return
        self.header_speed_running = True
        delay = random.uniform(1, 3)
        Clock.schedule_once(lambda dt: self._start_header_speed(), delay)

    def _start_header_speed(self):
        """启动头部实时算力显示"""
        def update(dt):
            enabled_pct = sum(
                f.get_power_value() for f in self.cards if f.is_locked)
            real_speed = int(self.current_speed * enabled_pct / 100)
            self.ids.header_speed.text = f'{real_speed:,}/s'
        Clock.schedule_interval(update, 1)

    def start_speed_animation(self):
        """速度动画定时器"""
        def animate(dt):
            self.current_speed = random.randint(395000, 405000)
            for card in self.cards:
                card.set_speed(self.current_speed)
        Clock.schedule_interval(animate, 0.05)

    def on_select_all(self):
        """全选/取消全选"""
        all_selected = all(c.is_selected for c in self.cards if not c.is_locked)
        new_state = not all_selected
        for card in self.cards:
            if not card.is_locked:
                card.is_selected = new_state

    def add_address(self):
        """新增地址卡片"""
        idx = len(self.cards)
        self._create_card(idx, 0)
        self.update_status()
        self.validate_power_total()
        self.save_config()
        # 滚动到底部
        Clock.schedule_once(lambda dt:
                            setattr(self.scroll_view, 'scroll_y', 0), 0.1)

    def import_addresses(self):
        """从剪贴板导入地址"""
        try:
            from kivy.core.clipboard import Clipboard
            content = Clipboard.get('text/plain') or Clipboard.get('')
            if not content:
                content = ''
        except Exception:
            content = ''

        if not content or not content.strip():
            show_warning_popup('提示', '剪贴板中没有内容')
            return

        addresses = [a.strip() for a in content.split('\n') if a.strip()]
        trc20_pattern = re.compile(r'^T[A-HJ-NP-Za-km-z1-9]{33}$')

        empty_cards = [c for c in self.cards
                       if not c.is_locked and not c.address.strip()]

        valid_count = 0
        for addr in addresses:
            if not trc20_pattern.match(addr):
                continue
            if empty_cards:
                card = empty_cards.pop(0)
                card.address = addr
            else:
                idx = len(self.cards)
                card = self._create_card(idx, 0)
                card.address = addr
            valid_count += 1

        self.update_status()
        self.validate_power_total()

        if valid_count > 0:
            show_info_popup('导入完成',
                            f'成功导入 {valid_count} 个地址')
        else:
            show_warning_popup('提示', '没有有效的 TRC-20 地址')

    def redistribute_power(self):
        """平均分配算力"""
        unlocked = [c for c in self.cards if not c.is_locked]
        if not unlocked:
            show_warning_popup('提示', '所有输入框已锁定')
            return

        count = len(unlocked)
        base = round(100.0 / count, 2)
        remainder = round(100.0 - base * (count - 1), 2)

        for i, card in enumerate(unlocked):
            power = remainder if i == count - 1 else base
            card._updating_power = True
            card.power = f'{power:.2f}'
            card._updating_power = False

        self.validate_power_total()
        self.save_config()
        show_info_popup('分配完成',
                        f'已为 {count} 个未锁定输入框平均分配算力')

    def delete_card(self, index):
        """删除指定卡片"""
        if index < len(self.cards):
            card = self.cards[index]
            self.card_container.remove_widget(card)
            self.cards.pop(index)
            # 重新索引
            for i, c in enumerate(self.cards):
                c.index = i
            self.update_status()
            self.validate_power_total()
            self.save_config()

    def batch_confirm(self):
        """批量确认选中卡片"""
        selected = [c for c in self.cards if c.is_selected and not c.is_locked]
        if not selected:
            show_warning_popup('提示', '请先选择要确认的地址')
            return

        for card in selected:
            addr = card.address.strip()
            if not addr:
                show_warning_popup(
                    '输入错误', f'目标地址 {card.index + 1} 未输入地址')
                return
            if not card.validate_trc20(addr):
                show_error_popup(
                    '格式错误', f'目标地址 {card.index + 1} 格式错误！')
                return

        valid, msg = self.validate_power_total(check_only=True)
        if not valid:
            show_warning_popup('算力校验失败', msg)
            return

        # 显示批量进度
        delay = random.uniform(2, 5)
        content = BoxLayout(orientation='vertical', padding=dp(24), spacing=dp(12))
        content.add_widget(Label(text='正在批量修改目标地址，请稍后...',
                                 font_size=sp(16),
                                 color=get_color_from_hex(TEXT_PRIMARY)))
        progress = ProgressBar(max=100, value=0, size_hint_y=None, height=dp(6))
        content.add_widget(progress)

        popup = Popup(title='正在修改目标地址',
                      title_size=sp(16),
                      content=content,
                      size_hint=(0.85, None),
                      height=dp(180),
                      background='',
                      auto_dismiss=False)
        popup.open()

        def on_ok():
            for card in selected:
                card.lock_input()
            self.update_status()

        def done(dt):
            popup.dismiss()
            show_confirm_popup('操作成功',
                               '目标地址已上传至服务器\n点击确认完成',
                               on_ok=on_ok)

        Clock.schedule_once(done, delay)

    def batch_cancel(self):
        """批量取消"""
        selected = [c for c in self.cards if c.is_selected]
        if not selected:
            show_warning_popup('提示', '请先选择要取消的地址')
            return

        for card in selected:
            if card.is_locked:
                card.unlock_input()
            else:
                card.address = ''
                card._updating_power = True
                card.power = '0.00'
                card._updating_power = False

        self.update_status()
        self.validate_power_total()
        self.save_config()
        show_info_popup('批量操作', f'已取消 {len(selected)} 个地址')

    def batch_clear(self):
        """批量清空"""
        selected = [c for c in self.cards if c.is_selected]
        if not selected:
            show_warning_popup('提示', '请先选择要清空的地址')
            return

        def on_ok():
            for card in selected:
                if not card.is_locked:
                    card.address = ''
                    card._updating_power = True
                    card.power = '0.00'
                    card._updating_power = False
            self.update_status()
            self.validate_power_total()
            self.save_config()
            show_info_popup(
                '批量操作', f'已清空 {len(selected)} 个输入框')

        show_confirm_popup('批量清空确认',
                           f'是否清空选中的 {len(selected)} 个输入框？',
                           ok_text='确定清空',
                           on_ok=on_ok)

    def validate_power_total(self, check_only=False):
        """验证算力总和"""
        total = round(sum(c.get_power_value() for c in self.cards), 2)

        if check_only:
            if abs(total - 100.0) > 0.001:
                return (False,
                        f'算力总和必须为 100.00％，当前 {total:.2f}％')
            return (True, '')

        # 更新状态栏
        if abs(total - 100.0) < 0.001:
            self.power_total_label.text = f'算力: {total:.2f}％'
            self.power_total_label.color = get_color_from_hex(SUCCESS)
        elif total > 100.0:
            self.power_total_label.text = f'超出 {total:.2f}％'
            self.power_total_label.color = get_color_from_hex(DANGER)
        else:
            self.power_total_label.text = f'还差 {100 - total:.2f}％'
            self.power_total_label.color = get_color_from_hex(WARNING)

        # 防抖保存
        self._schedule_save()

    def update_status(self):
        """更新状态栏"""
        total = len(self.cards)
        locked = sum(1 for c in self.cards if c.is_locked)
        self.status_label.text = f'地址: {total} | 锁定: {locked}'

    # ======================== 配置持久化 ========================
    def _get_config_path(self):
        """配置文件路径"""
        if platform == 'android':
            from android.storage import app_storage_path
            return os.path.join(app_storage_path(), 'config.json')
        elif getattr(sys, 'frozen', False):
            return os.path.join(os.path.dirname(sys.executable), 'config.json')
        else:
            return os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                'config.json')

    def _schedule_save(self):
        """防抖保存"""
        if self._save_pending:
            return
        self._save_pending = True
        Clock.schedule_once(lambda dt: self._do_save(), 2)

    def _do_save(self):
        self._save_pending = False
        self.save_config()

    def save_config(self):
        """保存配置"""
        data = {'addresses': []}
        for card in self.cards:
            data['addresses'].append({
                'address': card.address.strip(),
                'power': card.get_power_value(),
                'is_locked': card.is_locked,
            })
        try:
            os.makedirs(os.path.dirname(self._get_config_path()), exist_ok=True)
            with open(self._get_config_path(), 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def load_config(self):
        """加载配置"""
        config_path = self._get_config_path()
        if not os.path.exists(config_path):
            return
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception:
            return

        saved = data.get('addresses', [])
        if not saved:
            return

        # 清除现有卡片
        for card in self.cards[:]:
            self.card_container.remove_widget(card)
        self.cards.clear()

        # 重建
        for i, addr_data in enumerate(saved):
            power = addr_data.get('power', 0)
            card = self._create_card(i, power)
            addr = addr_data.get('address', '')
            if addr:
                card.address = addr
            if addr_data.get('is_locked', False):
                card.lock_input()

        self.update_status()
        self.validate_power_total()

    # ======================== 网络监控 ========================
    def _start_network_monitor(self):
        """后台网络监控"""
        def monitor():
            while not self._network_lost:
                time.sleep(5)
                if not check_network():
                    Clock.schedule_once(lambda dt: self._on_network_lost(), 0)
                    break

        t = threading.Thread(target=monitor, daemon=True)
        t.start()

    @mainthread
    def _on_network_lost(self):
        """网络断开回调"""
        if self._network_lost:
            return
        self._network_lost = True

        def on_dismiss(_):
            App.get_running_app().stop()

        show_error_popup('网络错误',
                         '连接服务器失败，程序即将退出。',
                         callback=on_dismiss)


class TRC20App(App):
    """Kivy 应用入口"""

    def build(self):
        Builder.load_string(KV)
        self.title = 'FATE ENDS 算力分配'

        # 网络检测
        if not check_network():
            show_error_popup('网络错误',
                             '连接服务器失败，请检查网络连接后重试。')
            Clock.schedule_once(lambda dt: self.stop(), 0.5)
            return BoxLayout()

        # 显示闪屏
        delay = random.randint(3, 10)
        self._show_splash(delay)
        return MainScreen(self)

    def _show_splash(self, delay):
        """显示启动闪屏"""
        splash_content = SplashScreen()
        popup = Popup(title='',
                      content=splash_content,
                      size_hint=(0.9, 0.7),
                      background='',
                      separator_color=(0, 0, 0, 0),
                      auto_dismiss=False)
        popup.open()

        # 模拟进度
        progress = splash_content.ids.splash_progress
        status = splash_content.ids.splash_status
        hint = splash_content.ids.splash_hint

        step = 100 / 10
        current = [0]

        def update(dt):
            current[0] += step
            progress.value = min(current[0], 100)
            hint.text = f'预计剩余 {max(0, int(delay - delay * current[0] / 100))} 秒'

        Clock.schedule_interval(update, delay / 10)

        def done(dt):
            Clock.unschedule(update)
            progress.value = 100
            status.text = '连接成功！'
            hint.text = '正在进入系统...'
            Clock.schedule_once(lambda dt2: popup.dismiss(), 0.8)

        Clock.schedule_once(done, delay + 0.1)


if __name__ == '__main__':
    from kivy.core.window import Window
    Window.softinput_mode = 'below_target'
    TRC20App().run()
