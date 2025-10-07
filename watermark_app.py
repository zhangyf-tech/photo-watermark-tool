import tkinter as tk
from tkinter import filedialog, messagebox, ttk, colorchooser
from PIL import Image, ImageDraw, ImageFont, ImageTk
import os


class WatermarkApp:
    def __init__(self):
        self.window = tk.Tk()
        self.window.title("照片水印工具 - Mac版")
        self.window.geometry("900x700")

        self.image_paths = []
        self.current_image_index = 0
        self.available_font = None
        self.watermark_color = "#FF0000"
        # 新增：记录当前预览图的原始尺寸和缩放比例
        self.current_original_size = None  # (原始宽, 原始高)
        self.current_scale_ratio = 1.0  # 当前缩放比例（相对于预览区域）

        # 初始化字体
        self.init_font()

        self.setup_ui()

    def init_font(self):
        """初始化可用的字体"""
        mac_fonts = [
            "/System/Library/Fonts/PingFang.ttc",  # 苹方，支持中文
            "/System/Library/Fonts/Helvetica.ttc",  # 系统默认
            "/System/Library/Fonts/Arial.ttf",  # Arial
        ]

        for font_path in mac_fonts:
            try:
                if font_path.endswith('.ttc'):
                    test_font = ImageFont.truetype(font_path, 20, index=0)
                    self.available_font = font_path
                    print(f"使用字体: {font_path}")
                    break
                else:
                    test_font = ImageFont.truetype(font_path, 20)
                    self.available_font = font_path
                    print(f"使用字体: {font_path}")
                    break
            except:
                continue

        if not self.available_font:
            print("警告: 使用默认字体")

    def get_font(self, size):
        """获取指定大小的字体"""
        if self.available_font:
            try:
                if self.available_font.endswith('.ttc'):
                    return ImageFont.truetype(self.available_font, size, index=0)
                else:
                    return ImageFont.truetype(self.available_font, size)
            except:
                return ImageFont.load_default()
        else:
            return ImageFont.load_default()

    def setup_ui(self):
        # 顶部按钮区域
        top_frame = tk.Frame(self.window)
        top_frame.pack(pady=10)

        tk.Button(top_frame, text="选择图片", command=self.select_images, width=15).pack(side=tk.LEFT, padx=5)
        tk.Button(top_frame, text="选择文件夹", command=self.select_folder, width=15).pack(side=tk.LEFT, padx=5)
        tk.Button(top_frame, text="删除选中图片", command=self.delete_selected_images, width=15).pack(side=tk.LEFT,
                                                                                                      padx=5)
        tk.Button(top_frame, text="导出图片", command=self.export_images, width=15).pack(side=tk.LEFT, padx=5)

        # 主内容区域
        main_frame = tk.Frame(self.window)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 左侧图片列表
        left_frame = tk.Frame(main_frame, width=200)
        left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        left_frame.pack_propagate(False)

        tk.Label(left_frame, text="图片列表", font=("Arial", 12, "bold")).pack(pady=5)

        self.image_listbox = tk.Listbox(left_frame, selectbackground="#4a86e8", selectforeground="white")
        self.image_listbox.pack(fill=tk.BOTH, expand=True)
        self.image_listbox.bind('<<ListboxSelect>>', self.on_image_select)

        # 右侧预览和设置
        right_frame = tk.Frame(main_frame)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # 预览区域（新增放大/缩小按钮）
        preview_control_frame = tk.Frame(right_frame)
        preview_control_frame.pack(fill=tk.X, pady=(0, 5))
        tk.Label(preview_control_frame, text="预览控制:").pack(side=tk.LEFT, padx=5)
        tk.Button(preview_control_frame, text="放大", command=self.zoom_in, width=8).pack(side=tk.LEFT, padx=3)
        tk.Button(preview_control_frame, text="缩小", command=self.zoom_out, width=8).pack(side=tk.LEFT, padx=3)
        tk.Button(preview_control_frame, text="重置大小", command=self.reset_zoom, width=8).pack(side=tk.LEFT, padx=3)

        # 预览容器（用于承载画布，实现图片居中显示）
        preview_container = tk.Frame(right_frame, height=400, bg='lightgray')
        preview_container.pack(fill=tk.X, pady=(0, 10))
        preview_container.pack_propagate(False)

        # 创建画布用于显示图片（支持定位）
        self.preview_canvas = tk.Canvas(preview_container, bg='lightgray', highlightthickness=0)
        self.preview_canvas.pack(expand=True, fill=tk.BOTH)
        # 初始显示提示文字
        self.preview_text_id = self.preview_canvas.create_text(
            preview_container.winfo_width() // 2, preview_container.winfo_height() // 2,
            text="图片预览区域", fill="gray", font=("Arial", 12)
        )

        # 水印设置区域
        settings_frame = tk.LabelFrame(right_frame, text="水印设置", padx=10, pady=10)
        settings_frame.pack(fill=tk.X)

        # 水印文字
        tk.Label(settings_frame, text="水印文字:").grid(row=0, column=0, sticky='w', pady=5)
        self.watermark_text = tk.Entry(settings_frame, width=30)
        self.watermark_text.grid(row=0, column=1, sticky='w', pady=5)
        self.watermark_text.insert(0, "测试水印")

        # 水印颜色选择
        tk.Label(settings_frame, text="水印颜色:").grid(row=0, column=2, sticky='w', pady=5, padx=10)
        self.color_preview = tk.Label(settings_frame, bg=self.watermark_color, width=5, bd=1, relief=tk.SUNKEN)
        self.color_preview.grid(row=0, column=3, sticky='w', pady=5)
        tk.Button(settings_frame, text="选择颜色", command=self.choose_watermark_color, width=10).grid(row=0, column=4,
                                                                                                       sticky='w',
                                                                                                       pady=5, padx=5)

        # 字体大小调节
        tk.Label(settings_frame, text="字体大小:").grid(row=1, column=0, sticky='w', pady=5)
        self.font_size_var = tk.IntVar(value=48)
        self.font_size_scale = tk.Scale(settings_frame, from_=12, to=120, orient=tk.HORIZONTAL,
                                        length=200, variable=self.font_size_var)
        self.font_size_scale.grid(row=1, column=1, sticky='w', pady=5)

        # 透明度
        tk.Label(settings_frame, text="透明度:").grid(row=1, column=2, sticky='w', pady=5, padx=10)
        self.opacity_scale = tk.Scale(settings_frame, from_=0, to=100, orient=tk.HORIZONTAL, length=200)
        self.opacity_scale.set(70)
        self.opacity_scale.grid(row=1, column=3, columnspan=2, sticky='w', pady=5)

        # 位置选择
        tk.Label(settings_frame, text="位置:").grid(row=2, column=0, sticky='w', pady=5)
        self.position_var = tk.StringVar(value="bottom-right")
        positions = [("左上", "top-left"), ("中上", "top-center"), ("右上", "top-right"),
                     ("左中", "middle-left"), ("居中", "center"), ("右中", "middle-right"),
                     ("左下", "bottom-left"), ("中下", "bottom-center"), ("右下", "bottom-right")]

        pos_frame = tk.Frame(settings_frame)
        pos_frame.grid(row=2, column=1, columnspan=4, sticky='w', pady=5)

        for i, (text, value) in enumerate(positions):
            rb = tk.Radiobutton(pos_frame, text=text, variable=self.position_var, value=value)
            rb.grid(row=i // 3, column=i % 3, sticky='w', padx=5)

        # 事件绑定
        self.watermark_text.bind('<KeyRelease>', self.on_settings_change)
        self.opacity_scale.configure(command=self.on_settings_change)
        self.position_var.trace('w', self.on_settings_change)
        self.font_size_scale.configure(command=self.on_settings_change)
        # 监听预览容器大小变化，自动调整图片位置
        preview_container.bind("<Configure>", self.on_preview_container_resize)

        # 更新按钮
        tk.Button(settings_frame, text="更新预览", command=self.force_update_preview,
                  bg='lightblue').grid(row=3, column=0, columnspan=5, pady=10)

        # 状态栏
        self.status_label = tk.Label(self.window, text="就绪", bd=1, relief=tk.SUNKEN, anchor=tk.W)
        self.status_label.pack(fill=tk.X, side=tk.BOTTOM)

    def on_settings_change(self, *args):
        if self.image_paths and self.current_image_index is not None:
            self.window.after(100, lambda: self.show_preview(self.current_image_index))

    def force_update_preview(self):
        if self.image_paths and self.current_image_index is not None:
            self.show_preview(self.current_image_index)

    def update_status(self, message):
        self.status_label.config(text=message)

    def select_images(self):
        files = filedialog.askopenfilenames(filetypes=[("图片文件", "*.jpg *.jpeg *.png *.bmp *.tiff")])
        if files:
            new_files = [f for f in files if f not in self.image_paths]
            self.image_paths.extend(new_files)
            self.update_image_list()
            if self.image_paths:
                self.reset_zoom()  # 重置缩放比例
                self.show_preview(0)
                self.update_status(f"已选择 {len(self.image_paths)} 张图片")

    def select_folder(self):
        folder = filedialog.askdirectory(title="选择图片文件夹")
        if folder:
            image_files = []
            for ext in ['*.jpg', '*.jpeg', '*.png', '*.bmp', '*.tiff']:
                ext_files = [os.path.join(folder, f) for f in os.listdir(folder)
                             if f.lower().endswith(ext[1:])]
                image_files.extend(ext_files)
            new_files = [f for f in image_files if f not in self.image_paths]
            self.image_paths.extend(new_files)
            self.update_image_list()
            if self.image_paths:
                self.reset_zoom()  # 重置缩放比例
                self.show_preview(0)
                self.update_status(f"已选择文件夹内 {len(self.image_paths)} 张图片")

    def update_image_list(self):
        self.image_listbox.delete(0, tk.END)
        for idx, path in enumerate(self.image_paths):
            filename = os.path.basename(path)
            self.image_listbox.insert(tk.END, f"{idx + 1}. {filename}")

    def on_image_select(self, event):
        selection = self.image_listbox.curselection()
        if selection:
            self.reset_zoom()  # 切换图片时重置缩放比例
            self.show_preview(selection[0])

    def choose_watermark_color(self):
        color = colorchooser.askcolor(title="选择水印颜色", initialcolor=self.watermark_color)
        if color[1]:
            self.watermark_color = color[1]
            self.color_preview.config(bg=self.watermark_color)
            self.on_settings_change()

    def delete_selected_images(self):
        selections = self.image_listbox.curselection()
        if not selections:
            messagebox.showwarning("警告", "请先在图片列表中选择要删除的图片")
            return

        for idx in reversed(selections):
            del self.image_paths[idx]

        self.update_image_list()
        if self.image_paths:
            self.reset_zoom()  # 删除后重置缩放比例
            self.show_preview(0)
            self.current_image_index = 0
        else:
            # 清空画布，显示提示文字
            self.preview_canvas.delete("all")
            self.preview_text_id = self.preview_canvas.create_text(
                self.preview_canvas.winfo_width() // 2, self.preview_canvas.winfo_height() // 2,
                text="图片预览区域", fill="gray", font=("Arial", 12)
            )
            self.current_image_index = None
            self.current_original_size = None
            self.current_scale_ratio = 1.0

        self.update_status(f"已删除 {len(selections)} 张图片，剩余 {len(self.image_paths)} 张")

    # ---------------------- 核心修复：原位置放大逻辑 ----------------------
    def calculate_initial_scale(self, original_width, original_height, container_width, container_height):
        """计算初始缩放比例（适配预览容器，不超过容器大小）"""
        if original_width == 0 or original_height == 0:
            return 1.0
        # 宽度比例和高度比例取最小值，确保图片完全放入容器
        width_ratio = container_width / original_width
        height_ratio = container_height / original_height
        return min(width_ratio, height_ratio) * 0.95  # 留5%边距

    def get_preview_container_size(self):
        """获取预览容器的当前大小（排除边框）"""
        return (self.preview_canvas.winfo_width(), self.preview_canvas.winfo_height())

    def update_preview_image(self, image):
        """更新画布上的图片，确保居中显示（无偏移）"""
        # 清空画布（保留提示文字外的所有元素）
        self.preview_canvas.delete("all")

        # 处理空图片情况
        if image is None:
            self.preview_text_id = self.preview_canvas.create_text(
                self.preview_canvas.winfo_width() // 2, self.preview_canvas.winfo_height() // 2,
                text="图片预览区域", fill="gray", font=("Arial", 12)
            )
            return

        # 获取图片原始尺寸和预览容器尺寸
        img_width, img_height = image.size
        container_width, container_height = self.get_preview_container_size()

        # 计算缩放后的图片尺寸
        scaled_width = int(img_width * self.current_scale_ratio)
        scaled_height = int(img_height * self.current_scale_ratio)

        # 计算图片居中坐标（关键：基于容器中心和图片中心对齐，避免偏移）
        x = (container_width - scaled_width) // 2  # 水平居中
        y = (container_height - scaled_height) // 2  # 垂直居中

        # 转换为Tkinter可用格式并显示
        self.tk_image = ImageTk.PhotoImage(image.resize((scaled_width, scaled_height), Image.Resampling.LANCZOS))
        self.preview_canvas.create_image(x, y, anchor=tk.NW, image=self.tk_image, tags="preview_img")

    def on_preview_container_resize(self, event):
        """预览容器大小变化时，重新调整图片位置"""
        if self.current_original_size and self.image_paths and self.current_image_index is not None:
            # 重新计算初始缩放比例（适配新容器大小）
            original_width, original_height = self.current_original_size
            container_width, container_height = event.width, event.height
            self.current_scale_ratio = self.calculate_initial_scale(original_width, original_height, container_width,
                                                                    container_height)
            # 重新加载并显示图片
            self.show_preview(self.current_image_index)

    def zoom_in(self):
        """放大图片（原位置放大，每次增加20%比例）"""
        if not self.current_original_size or not self.image_paths:
            return
        # 限制最大缩放比例（不超过原始尺寸的3倍，避免过度放大模糊）
        max_scale = 3.0
        if self.current_scale_ratio < max_scale:
            self.current_scale_ratio *= 1.2
            self.show_preview(self.current_image_index)
            self.update_status(f"当前缩放比例: {int(self.current_scale_ratio * 100)}%")

    def zoom_out(self):
        """缩小图片（原位置缩小，每次减少20%比例）"""
        if not self.current_original_size or not self.image_paths:
            return
        # 限制最小缩放比例（不小于初始比例的50%，避免过度缩小）
        min_scale = self.calculate_initial_scale(
            self.current_original_size[0], self.current_original_size[1],
            *self.get_preview_container_size()
        ) * 0.5
        if self.current_scale_ratio > min_scale:
            self.current_scale_ratio *= 0.8
            self.show_preview(self.current_image_index)
            self.update_status(f"当前缩放比例: {int(self.current_scale_ratio * 100)}%")

    def reset_zoom(self):
        """重置图片大小为初始适配尺寸"""
        if self.current_original_size:
            container_width, container_height = self.get_preview_container_size()
            self.current_scale_ratio = self.calculate_initial_scale(
                self.current_original_size[0], self.current_original_size[1],
                container_width, container_height
            )
            if self.image_paths and self.current_image_index is not None:
                self.show_preview(self.current_image_index)
            self.update_status(f"缩放比例已重置")

    # -------------------------------------------------------------------

    def show_preview(self, index):
        try:
            self.current_image_index = index
            image_path = self.image_paths[index]

            # 加载原图并记录原始尺寸（用于缩放计算）
            original_image = Image.open(image_path)
            self.current_original_size = original_image.size  # 保存原始尺寸
            img_width, img_height = original_image.size

            # 添加水印（预览时字体大小按缩放比例调整，确保水印与图片比例一致）
            watermark_text = self.watermark_text.get()
            if watermark_text:
                # 预览水印字体大小 = 导出字体大小 * 当前缩放比例（保持视觉一致）
                preview_font_size = int(self.font_size_var.get() * self.current_scale_ratio)
                preview_image = self.add_watermark_to_image(original_image, watermark_text, preview=True,
                                                            preview_font_size=preview_font_size)
            else:
                preview_image = original_image.copy()

            # 更新预览图片（核心：居中显示，无偏移）
            self.update_preview_image(preview_image)

            # 更新状态栏
            filename = os.path.basename(image_path)
            scale_percent = int(self.current_scale_ratio * 100)
            self.update_status(
                f"正在预览: {filename} (共{len(self.image_paths)}张，当前第{index + 1}张，缩放{scale_percent}%)")

        except Exception as e:
            messagebox.showerror("错误", f"无法加载图片: {str(e)}")

    def add_watermark_to_image(self, image, watermark_text, preview=False, preview_font_size=None):
        if image.mode != 'RGBA':
            image = image.convert('RGBA')

        watermark_layer = Image.new('RGBA', image.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(watermark_layer)

        # 确定字体大小（预览用调整后的大小，导出用设置大小）
        if preview and preview_font_size:
            font_size = preview_font_size
        else:
            font_size = self.font_size_var.get()

        font = self.get_font(font_size)

        # 计算水印位置（基于原始图片尺寸，确保位置准确）
        position = self.calculate_position(image.size, draw, watermark_text, font)

        # 转换颜色（十六进制转RGB）
        r = int(self.watermark_color[1:3], 16)
        g = int(self.watermark_color[3:5], 16)
        b = int(self.watermark_color[5:7], 16)
        opacity = int(255 * (self.opacity_scale.get() / 100))

        # 绘制水印文字
        draw.text(position, watermark_text, font=font, fill=(r, g, b, opacity))

        # 合并图层
        watermarked = Image.alpha_composite(image, watermark_layer)
        return watermarked

    def calculate_position(self, image_size, draw, text, font):
        width, height = image_size

        # 精确计算文字尺寸
        try:
            bbox = draw.textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
        except:
            text_width = len(text) * font.size * 0.5
            text_height = font.size * 1.2

        # 动态边距（避免水印贴边）
        margin = min(width, height) * 0.02
        if margin < 10:
            margin = 10

        # 位置映射（基于原始图片尺寸计算，确保位置准确）
        position_map = {
            "top-left": (margin, margin),
            "top-center": ((width - text_width) // 2, margin),
            "top-right": (width - text_width - margin, margin),
            "middle-left": (margin, (height - text_height) // 2),
            "center": ((width - text_width) // 2, (height - text_height) // 2),
            "middle-right": (width - text_width - margin, (height - text_height) // 2),
            "bottom-left": (margin, height - text_height - margin),
            "bottom-center": ((width - text_width) // 2, height - text_height - margin),
            "bottom-right": (width - text_width - margin, height - text_height - margin)
        }

        return position_map[self.position_var.get()]

    def export_images(self):
        if not self.image_paths:
            messagebox.showwarning("警告", "请先选择图片")
            return
        watermark_text = self.watermark_text.get().strip()
        if not watermark_text:
            messagebox.showwarning("警告", "请输入水印文字")
            return
        output_dir = filedialog.askdirectory(title="选择输出文件夹")
        if not output_dir:
            return

        try:
            success_count = 0
            total = len(self.image_paths)
            for i, image_path in enumerate(self.image_paths, 1):
                if self.process_single_image(image_path, output_dir, watermark_text):
                    success_count += 1
                self.update_status(f"正在导出: {i}/{total} (成功{success_count}张)")
                self.window.update()

            messagebox.showinfo("完成", f"导出完成！\n成功处理 {success_count}/{total} 张图片\n输出路径: {output_dir}")
            self.update_status(f"导出完成，成功{success_count}张，失败{total - success_count}张")

        except Exception as e:
            messagebox.showerror("错误", f"批量处理失败: {str(e)}")
            self.update_status(f"导出失败: {str(e)}")

    def process_single_image(self, image_path, output_dir, watermark_text):
        try:
            original = Image.open(image_path)
            watermarked = self.add_watermark_to_image(original, watermark_text, preview=False)

            filename = os.path.basename(image_path)
            name, ext = os.path.splitext(filename)
            output_filename = f"watermarked_{name}{ext}"
            output_path = os.path.join(output_dir, output_filename)

            # 按格式保存
            if ext.lower() in ['.png']:
                watermarked.save(output_path, "PNG", compress_level=6)
            else:
                watermarked.convert("RGB").save(output_path, "JPEG", quality=95)

            return True
        except Exception as e:
            print(f"处理图片 {os.path.basename(image_path)} 时出错: {str(e)}")
            return False

    def run(self):
        self.window.mainloop()


if __name__ == "__main__":
    app = WatermarkApp()
    app.run()