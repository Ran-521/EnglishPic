import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk, ImageChops, ImageDraw
import time
import threading
import json

class EnglishPicProcessor:
    def __init__(self, root):
        self.root = root
        self.root.title("图片批量处理工具")
        self.root.geometry("1200x800")
        
        # 配置文件路径
        self.config_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")
        
        # 设置固定路径
        self.base_img_path = "E:\\Onedrive\\KMS\\10-英语音频\\赵老师做好的\\01-图片\\back.png"
        # 使用修改后的文件名
        self.title_img_path = r"E:\Onedrive\KMS\10-英语音频\赵老师做好的\01-图片\只是标题.png"
        # 恢复背景覆盖图路径
        self.overlay_img_path = "E:\\Onedrive\\KMS\\10-英语音频\\赵老师做好的\\01-图片\\背景图片.png"
        # 添加顶层图片路径
        self.top_img_path = r"E:\Onedrive\KMS\10-英语音频\赵老师做好的\01-图片\真的只是标题.png"
        
        # 调试标志
        self.debug_mode = True
        
        # 初始化变量
        self.selected_images = []  # 选择的图片列表
        self.current_image_index = 0  # 当前预览的图片索引
        self.original_images = {}  # 存储原始图片（调整宽度后的）
        
        # 图片处理参数
        self.scale_factor = tk.StringVar(value="100")  # 放大比例（百分比）
        self.x_offset = tk.StringVar(value="0")  # 水平偏移
        self.y_offset = tk.StringVar(value="0")  # 垂直偏移
        self.overlay_scale_factor = tk.StringVar(value="100")  # 背景覆盖图放大比例（百分比）
        self.crop_bottom_percent = tk.StringVar(value="10")  # 底部裁剪比例（百分比）
        self.crop_right_percent = tk.StringVar(value="10")  # 右侧裁剪比例（百分比）
        self.crop_top_percent = tk.StringVar(value="10")  # 上方裁剪比例（百分比）
        self.crop_corner_size = tk.StringVar(value="15")  # 右上角正方形裁剪大小（百分比）
        self.use_corner_crop = tk.BooleanVar(value=False)  # 是否启用右上角裁剪
        
        # 图层启用控制变量
        self.use_base_img = tk.BooleanVar(value=True)  # 是否使用底图
        self.use_title_img = tk.BooleanVar(value=True)  # 是否使用标题/遮挡图
        self.use_overlay_img = tk.BooleanVar(value=True)  # 是否使用背景覆盖图
        self.use_top_img = tk.BooleanVar(value=True)  # 是否使用顶层图片
        
        # 加载之前的配置
        self.load_config()
        
        # 防抖动变量
        self.update_pending = False  # 是否有更新等待中
        
        # 创建界面
        self.create_widgets()
        
        # 验证固定路径图片是否存在
        self.verify_fixed_images()
        
        # 缓存图像资源
        self.cache_resources()
        
        # 设置窗口关闭事件，用于保存配置
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def cache_resources(self):
        """缓存常用图像资源以提高性能"""
        self.cached_images = {}
        
        # 加载底图
        try:
            if os.path.exists(self.base_img_path):
                self.cached_images['base'] = Image.open(self.base_img_path).convert("RGBA")
                if self.debug_mode:
                    print(f"底图加载成功: {self.base_img_path}")
            else:
                if self.debug_mode:
                    print(f"底图路径不存在: {self.base_img_path}")
        except Exception as e:
            messagebox.showerror("缓存错误", f"加载底图时出错: {str(e)}")
            if self.debug_mode:
                print(f"底图加载错误: {str(e)}")
        
        # 加载标题/遮挡图
        try:
            if os.path.exists(self.title_img_path):
                self.cached_images['title'] = Image.open(self.title_img_path).convert("RGBA")
                if self.debug_mode:
                    print(f"标题图加载成功: {self.title_img_path}")
            else:
                if self.debug_mode:
                    print(f"标题图路径不存在: {self.title_img_path}")
        except Exception as e:
            messagebox.showerror("缓存错误", f"加载标题/遮挡图时出错: {str(e)}")
            if self.debug_mode:
                print(f"标题图加载错误: {str(e)}")
        
        # 加载背景覆盖图
        try:
            if os.path.exists(self.overlay_img_path):
                self.cached_images['overlay'] = Image.open(self.overlay_img_path).convert("RGBA")
                if self.debug_mode:
                    print(f"背景覆盖图加载成功: {self.overlay_img_path}")
            else:
                if self.debug_mode:
                    print(f"背景覆盖图路径不存在: {self.overlay_img_path}")
        except Exception as e:
            messagebox.showerror("缓存错误", f"加载背景覆盖图时出错: {str(e)}")
            if self.debug_mode:
                print(f"背景覆盖图加载错误: {str(e)}")
        
        # 加载顶层图片
        try:
            if os.path.exists(self.top_img_path):
                self.cached_images['top'] = Image.open(self.top_img_path).convert("RGBA")
                if self.debug_mode:
                    print(f"顶层图片加载成功: {self.top_img_path}")
            else:
                if self.debug_mode:
                    print(f"顶层图片路径不存在: {self.top_img_path}")
        except Exception as e:
            messagebox.showerror("缓存错误", f"加载顶层图片时出错: {str(e)}")
            if self.debug_mode:
                print(f"顶层图片加载错误: {str(e)}")
    
    def verify_fixed_images(self):
        """验证固定路径的图片是否存在"""
        missing_files = []
        if not os.path.exists(self.base_img_path):
            missing_files.append(f"底图: {self.base_img_path}")
        if not os.path.exists(self.title_img_path):
            missing_files.append(f"标题/遮挡图: {self.title_img_path}")
        if not os.path.exists(self.overlay_img_path):
            missing_files.append(f"背景覆盖图: {self.overlay_img_path}")
        if not os.path.exists(self.top_img_path):
            missing_files.append(f"顶层图片: {self.top_img_path}")
        
        if missing_files:
            error_msg = "以下文件路径不存在:\n\n" + "\n".join(missing_files)
            messagebox.showerror("文件路径错误", error_msg)
    
    def create_widgets(self):
        """创建GUI界面"""
        # 创建框架
        left_frame = ttk.Frame(self.root, padding=10)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=False)
        
        right_frame = ttk.Frame(self.root, padding=10)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # 左侧操作区 - 显示已使用的固定路径
        ttk.Label(left_frame, text="图片路径:").grid(row=0, column=0, sticky=tk.W, pady=(0, 5))
        
        # 底图路径和选择按钮
        ttk.Label(left_frame, text="底图:").grid(row=1, column=0, sticky=tk.W, pady=(0, 5), padx=(20, 0))
        use_base_check = ttk.Checkbutton(left_frame, variable=self.use_base_img, command=self.update_preview)
        use_base_check.grid(row=1, column=0, sticky=tk.E, padx=(0, 5))
        self.base_path_label = ttk.Label(left_frame, text=os.path.basename(self.base_img_path))
        self.base_path_label.grid(row=1, column=1, sticky=tk.W)
        ttk.Button(left_frame, text="浏览...", command=lambda: self.select_image_path("base")).grid(row=1, column=2, padx=5)
        
        # 标题/遮挡图路径和选择按钮
        ttk.Label(left_frame, text="标题/遮挡图:").grid(row=2, column=0, sticky=tk.W, pady=(0, 5), padx=(20, 0))
        use_title_check = ttk.Checkbutton(left_frame, variable=self.use_title_img, command=self.update_preview)
        use_title_check.grid(row=2, column=0, sticky=tk.E, padx=(0, 5))
        self.title_path_label = ttk.Label(left_frame, text=os.path.basename(self.title_img_path))
        self.title_path_label.grid(row=2, column=1, sticky=tk.W)
        ttk.Button(left_frame, text="浏览...", command=lambda: self.select_image_path("title")).grid(row=2, column=2, padx=5)
        
        # 背景覆盖图路径和选择按钮
        ttk.Label(left_frame, text="背景覆盖图:").grid(row=3, column=0, sticky=tk.W, pady=(0, 5), padx=(20, 0))
        use_overlay_check = ttk.Checkbutton(left_frame, variable=self.use_overlay_img, command=self.update_preview)
        use_overlay_check.grid(row=3, column=0, sticky=tk.E, padx=(0, 5))
        self.overlay_path_label = ttk.Label(left_frame, text=os.path.basename(self.overlay_img_path))
        self.overlay_path_label.grid(row=3, column=1, sticky=tk.W)
        ttk.Button(left_frame, text="浏览...", command=lambda: self.select_image_path("overlay")).grid(row=3, column=2, padx=5)
        
        # 添加顶层图片路径和选择按钮
        ttk.Label(left_frame, text="顶层图片:").grid(row=4, column=0, sticky=tk.W, pady=(0, 5), padx=(20, 0))
        use_top_check = ttk.Checkbutton(left_frame, variable=self.use_top_img, command=self.update_preview)
        use_top_check.grid(row=4, column=0, sticky=tk.E, padx=(0, 5))
        self.top_path_label = ttk.Label(left_frame, text=os.path.basename(self.top_img_path))
        self.top_path_label.grid(row=4, column=1, sticky=tk.W)
        ttk.Button(left_frame, text="浏览...", command=lambda: self.select_image_path("top")).grid(row=4, column=2, padx=5)
        
        # 选择需要处理的图片
        ttk.Separator(left_frame, orient=tk.HORIZONTAL).grid(row=5, column=0, columnspan=2, sticky=tk.EW, pady=10)
        
        ttk.Label(left_frame, text="选择需要处理的图片:").grid(row=6, column=0, columnspan=2, sticky=tk.W, pady=(10, 5))
        ttk.Button(left_frame, text="浏览...", command=self.select_images).grid(row=7, column=0, columnspan=2, sticky=tk.W)
        
        ttk.Label(left_frame, text="选择的图片数量: 0").grid(row=8, column=0, columnspan=2, sticky=tk.W, pady=(5, 20))
        self.image_count_label = left_frame.grid_slaves(row=8, column=0)[0]
        
        # 参数调整区域
        ttk.Separator(left_frame, orient=tk.HORIZONTAL).grid(row=9, column=0, columnspan=2, sticky=tk.EW, pady=10)
        
        ttk.Label(left_frame, text="调整参数:").grid(row=10, column=0, columnspan=2, sticky=tk.W, pady=(10, 5))
        
        # 图片放大比例输入框 (百分比)
        ttk.Label(left_frame, text="图片放大比例(%):").grid(row=11, column=0, sticky=tk.W, padx=(20, 0))
        scale_entry = ttk.Entry(left_frame, textvariable=self.scale_factor, width=10)
        scale_entry.grid(row=11, column=1, padx=5, sticky=tk.W)
        
        # 水平偏移输入框
        ttk.Label(left_frame, text="水平偏移(像素):").grid(row=12, column=0, sticky=tk.W, pady=(10, 0), padx=(20, 0))
        offset_entry = ttk.Entry(left_frame, textvariable=self.x_offset, width=10)
        offset_entry.grid(row=12, column=1, padx=5, pady=(10, 0), sticky=tk.W)
        
        # 垂直偏移输入框
        ttk.Label(left_frame, text="垂直偏移(像素):").grid(row=13, column=0, sticky=tk.W, pady=(10, 0), padx=(20, 0))
        y_offset_entry = ttk.Entry(left_frame, textvariable=self.y_offset, width=10)
        y_offset_entry.grid(row=13, column=1, padx=5, pady=(10, 0), sticky=tk.W)
        
        # 上方裁剪比例输入框
        ttk.Label(left_frame, text="上方裁剪比例(%):").grid(row=14, column=0, sticky=tk.W, pady=(10, 0), padx=(20, 0))
        crop_top_entry = ttk.Entry(left_frame, textvariable=self.crop_top_percent, width=10)
        crop_top_entry.grid(row=14, column=1, padx=5, pady=(10, 0), sticky=tk.W)
        
        # 底部裁剪比例输入框
        ttk.Label(left_frame, text="底部裁剪比例(%):").grid(row=15, column=0, sticky=tk.W, pady=(10, 0), padx=(20, 0))
        crop_entry = ttk.Entry(left_frame, textvariable=self.crop_bottom_percent, width=10)
        crop_entry.grid(row=15, column=1, padx=5, pady=(10, 0), sticky=tk.W)
        
        # 右侧裁剪比例输入框
        ttk.Label(left_frame, text="右侧裁剪比例(%):").grid(row=16, column=0, sticky=tk.W, pady=(10, 0), padx=(20, 0))
        crop_right_entry = ttk.Entry(left_frame, textvariable=self.crop_right_percent, width=10)
        crop_right_entry.grid(row=16, column=1, padx=5, pady=(10, 0), sticky=tk.W)
        
        # 添加右上角裁剪控件
        ttk.Separator(left_frame, orient=tk.HORIZONTAL).grid(row=17, column=0, columnspan=2, sticky=tk.EW, pady=10)
        
        # 右上角裁剪框架
        corner_frame = ttk.Frame(left_frame)
        corner_frame.grid(row=18, column=0, columnspan=2, sticky=tk.W, pady=(10, 0))
        
        # 右上角裁剪复选框
        corner_check = ttk.Checkbutton(corner_frame, text="启用右上角裁剪", variable=self.use_corner_crop, command=self.update_preview)
        corner_check.pack(side=tk.LEFT, padx=(0, 10))
        
        # 右上角裁剪大小输入框
        ttk.Label(corner_frame, text="裁剪大小(%):").pack(side=tk.LEFT, padx=(10, 5))
        corner_size_entry = ttk.Entry(corner_frame, textvariable=self.crop_corner_size, width=10)
        corner_size_entry.pack(side=tk.LEFT)
        
        # 背景覆盖图放大比例输入框 (百分比)
        ttk.Label(left_frame, text="背景覆盖图放大比例(%):").grid(row=19, column=0, sticky=tk.W, pady=(10, 0), padx=(20, 0))
        overlay_entry = ttk.Entry(left_frame, textvariable=self.overlay_scale_factor, width=10)
        overlay_entry.grid(row=19, column=1, padx=5, pady=(10, 0), sticky=tk.W)
        
        # 添加应用按钮，用于确认调整并更新预览
        ttk.Button(left_frame, text="应用调整", command=self.update_preview).grid(row=20, column=0, columnspan=2, pady=(10, 0))
        
        # 预览和导出按钮
        ttk.Separator(left_frame, orient=tk.HORIZONTAL).grid(row=21, column=0, columnspan=2, sticky=tk.EW, pady=10)
        
        preview_frame = ttk.Frame(left_frame)
        preview_frame.grid(row=22, column=0, columnspan=2, pady=(10, 0))
        
        ttk.Button(preview_frame, text="上一张", command=self.prev_image).pack(side=tk.LEFT, padx=5)
        ttk.Button(preview_frame, text="下一张", command=self.next_image).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(left_frame, text="批量导出", command=self.batch_process).grid(row=23, column=0, columnspan=2, pady=(20, 0))
        
        # 右侧预览区
        self.preview_label = ttk.Label(right_frame, text="预览区域 - 请选择图片")
        self.preview_label.pack(fill=tk.BOTH, expand=True)
    
    def select_images(self):
        """批量选择需要处理的图片"""
        file_paths = filedialog.askopenfilenames(
            title="选择需要处理的图片",
            filetypes=[("图片文件", "*.png;*.jpg;*.jpeg")]
        )
        if file_paths:
            self.selected_images = list(file_paths)
            self.image_count_label.config(text=f"选择的图片数量: {len(self.selected_images)}")
            self.current_image_index = 0
            self.original_images = {}  # 清空原始图片缓存
            self.update_preview()
    
    def select_image_path(self, image_type):
        """选择图片路径"""
        file_path = filedialog.askopenfilename(
            title=f"选择{image_type}图片",
            filetypes=[("图片文件", "*.png;*.jpg;*.jpeg")]
        )
        if file_path:
            if image_type == "base":
                self.base_img_path = file_path
                self.base_path_label.config(text=os.path.basename(file_path))
            elif image_type == "title":
                self.title_img_path = file_path
                self.title_path_label.config(text=os.path.basename(file_path))
            elif image_type == "overlay":
                self.overlay_img_path = file_path
                self.overlay_path_label.config(text=os.path.basename(file_path))
            elif image_type == "top":
                self.top_img_path = file_path
                self.top_path_label.config(text=os.path.basename(file_path))
            
            # 清空缓存，重新加载资源
            self.original_images = {}  # 清空原始图片缓存
            self.cached_images = {}  # 清空缓存图像
            self.cache_resources()  # 重新缓存资源
            
            # 如果有选定的图片，更新预览
            if self.selected_images:
                self.update_preview()
    
    def get_original_image(self, img_path):
        """获取处理过的原始图片（调整宽度适应底图）"""
        if img_path in self.original_images:
            return self.original_images[img_path].copy()
        
        try:
            # 加载原图并调整为底图宽度
            if 'base' in self.cached_images:
                base_width = self.cached_images['base'].width
                img = Image.open(img_path).convert("RGBA")
                
                # 计算等比例缩放后的高度
                width_percent = base_width / float(img.width)
                new_height = int(float(img.height) * float(width_percent))
                
                # 调整图片大小
                resized_img = img.resize((base_width, new_height), Image.LANCZOS)
                
                # 裁剪上方
                try:
                    crop_top_percent = float(self.crop_top_percent.get()) / 100.0
                    if crop_top_percent > 0 and crop_top_percent < 1:
                        # 计算要裁剪的高度
                        crop_top_height = int(resized_img.height * crop_top_percent)
                        # 裁剪图片 (left, top, right, bottom)
                        resized_img = resized_img.crop((0, crop_top_height, resized_img.width, resized_img.height))
                        if self.debug_mode:
                            print(f"已裁剪上方 {crop_top_percent*100}% 的图片")
                except ValueError:
                    messagebox.showerror("参数错误", "上方裁剪比例必须是有效的数字")
                
                # 裁剪底部
                try:
                    crop_percent = float(self.crop_bottom_percent.get()) / 100.0
                    if crop_percent > 0 and crop_percent < 1:
                        # 计算要保留的高度
                        crop_height = int(resized_img.height * (1 - crop_percent))
                        # 裁剪图片 (left, top, right, bottom)
                        resized_img = resized_img.crop((0, 0, resized_img.width, crop_height))
                        if self.debug_mode:
                            print(f"已裁剪底部 {crop_percent*100}% 的图片")
                except ValueError:
                    messagebox.showerror("参数错误", "裁剪比例必须是有效的数字")
                
                # 裁剪右侧
                try:
                    crop_right_percent = float(self.crop_right_percent.get()) / 100.0
                    if crop_right_percent > 0 and crop_right_percent < 1:
                        # 计算要保留的宽度
                        crop_width = int(resized_img.width * (1 - crop_right_percent))
                        # 裁剪图片 (left, top, right, bottom)
                        resized_img = resized_img.crop((0, 0, crop_width, resized_img.height))
                        if self.debug_mode:
                            print(f"已裁剪右侧 {crop_right_percent*100}% 的图片")
                except ValueError:
                    messagebox.showerror("参数错误", "右侧裁剪比例必须是有效的数字")
                
                # 右上角正方形区域裁剪（如果启用）- 修复版本
                if self.use_corner_crop.get():
                    try:
                        corner_size_percent = float(self.crop_corner_size.get()) / 100.0
                        if corner_size_percent > 0 and corner_size_percent < 1:
                            # 计算正方形的尺寸（基于图片宽度）
                            square_size = int(resized_img.width * corner_size_percent)
                            if square_size > 0:
                                # 创建一个与图像大小相同的RGBA图像作为副本
                                result_img = Image.new("RGBA", resized_img.size, (0, 0, 0, 0))
                                
                                # 将原始图像粘贴到结果图像上
                                result_img.paste(resized_img, (0, 0), resized_img)
                                
                                # 创建一个绘图对象
                                draw = ImageDraw.Draw(result_img)
                                
                                # 直接在右上角绘制一个完全透明的矩形
                                draw.rectangle(
                                    [(resized_img.width - square_size, 0), 
                                     (resized_img.width, square_size)],
                                    fill=(0, 0, 0, 0)  # 完全透明
                                )
                                
                                # 使用修改后的图像
                                resized_img = result_img
                                
                                if self.debug_mode:
                                    print(f"已裁剪右上角 {corner_size_percent*100}% 大小的正方形区域")
                    except ValueError:
                        messagebox.showerror("参数错误", "右上角裁剪大小必须是有效的数字")
                
                # 缓存处理后的图片
                self.original_images[img_path] = resized_img
                return resized_img.copy()
            else:
                return None
        except Exception as e:
            messagebox.showerror("处理错误", f"调整图片尺寸时出错: {str(e)}")
            if self.debug_mode:
                import traceback
                traceback.print_exc()
            return None
    
    def update_preview(self, *args):
        """更新预览图像"""
        self.update_pending = False
        
        if 'base' not in self.cached_images or not self.selected_images:
            return
        
        # 获取当前预览的图片
        if 0 <= self.current_image_index < len(self.selected_images):
            img_path = self.selected_images[self.current_image_index]
            
            # 使用单独的线程处理图片
            self.preview_label.config(text="正在处理预览...")
            
            def process_and_update():
                # 处理图片
                processed_img = self.process_image(img_path)
                if processed_img:
                    # 调整预览大小
                    preview_w, preview_h = 700, 600
                    preview_img = processed_img.copy()
                    preview_img.thumbnail((preview_w, preview_h), Image.LANCZOS)
                    
                    # 使用主线程更新UI
                    def update_ui():
                        # 显示预览
                        photo = ImageTk.PhotoImage(preview_img)
                        self.preview_label.config(image=photo)
                        self.preview_label.image = photo  # 保持引用以防止被垃圾回收
                    
                    self.root.after(0, update_ui)
            
            # 启动处理线程
            processing_thread = threading.Thread(target=process_and_update)
            processing_thread.daemon = True
            processing_thread.start()
    
    def process_image(self, img_path):
        """处理单张图片"""
        try:
            # 创建初始图像（如果不使用底图，则创建透明图像）
            if self.use_base_img.get() and 'base' in self.cached_images:
                result = self.cached_images['base'].copy()
            else:
                # 如果不使用底图，创建一个透明的画布
                if 'base' in self.cached_images:
                    base_size = self.cached_images['base'].size
                else:
                    # 如果没有底图缓存，使用默认大小
                    base_size = (1920, 1080)
                result = Image.new("RGBA", base_size, (0, 0, 0, 0))
            
            # 获取已调整宽度的图片
            img_resized = self.get_original_image(img_path)
            if img_resized is None:
                return None
            
            # 应用用户定义的缩放（百分比转换为小数）
            try:
                scale_percent = float(self.scale_factor.get()) / 100.0
                x_offset = int(self.x_offset.get())
                y_offset = int(self.y_offset.get())  # 获取垂直偏移
            except ValueError:
                messagebox.showerror("参数错误", "请输入有效的数字")
                return None
            
            if scale_percent <= 0:
                messagebox.showerror("参数错误", "放大比例必须大于0")
                return None
            
            # 应用缩放
            if scale_percent != 1.0:
                new_width = int(img_resized.width * scale_percent)
                new_height = int(img_resized.height * scale_percent)
                img_resized = img_resized.resize((new_width, new_height), Image.LANCZOS)
            
            # 计算图片位置 (居中 + x偏移 + y偏移)
            x = (result.width - img_resized.width) // 2 + x_offset
            y = (result.height - img_resized.height) // 2 + y_offset  # 添加y偏移
            
            # 创建一个与结果大小相同的透明图像来粘贴用户图片
            user_img_layer = Image.new("RGBA", result.size, (0, 0, 0, 0))
            user_img_layer.paste(img_resized, (x, y), img_resized)
            
            # 合并底图和用户图片
            result = Image.alpha_composite(result, user_img_layer)
            
            # 添加标题/遮挡图 - 先添加标题/遮挡图（仅当启用时）
            if self.use_title_img.get() and 'title' in self.cached_images:
                title_img = self.cached_images['title'].copy()
                if self.debug_mode:
                    print("正在添加标题/遮挡图")
                    print(f"标题图尺寸: {title_img.width}x{title_img.height}")
                    print(f"结果图尺寸: {result.width}x{result.height}")
                
                # 创建标题图层并粘贴
                title_layer = Image.new("RGBA", result.size, (0, 0, 0, 0))
                title_layer.paste(title_img, (0, 0), title_img)
                
                # 使用alpha合成添加标题图
                result = Image.alpha_composite(result, title_layer)
            elif self.debug_mode and self.use_title_img.get():
                print("标题/遮挡图未在缓存中找到")
            
            # 添加背景覆盖图（使用自定义混合模式）- 最后添加，放在最顶层（仅当启用时）
            if self.use_overlay_img.get() and 'overlay' in self.cached_images:
                overlay_img = self.cached_images['overlay'].copy()
                
                # 应用背景覆盖图缩放（百分比转换为小数）
                try:
                    overlay_scale_percent = float(self.overlay_scale_factor.get()) / 100.0
                except ValueError:
                    messagebox.showerror("参数错误", "请输入有效的数字")
                    return None
                
                if overlay_scale_percent <= 0:
                    messagebox.showerror("参数错误", "背景覆盖图放大比例必须大于0")
                    return None
                
                # 调整覆盖图大小
                overlay_w = int(overlay_img.width * overlay_scale_percent)
                overlay_h = int(overlay_img.height * overlay_scale_percent)
                overlay_resized = overlay_img.resize((overlay_w, overlay_h), Image.LANCZOS)
                
                # 计算覆盖图位置（居中）
                overlay_x = (result.width - overlay_w) // 2
                overlay_y = (result.height - overlay_h) // 2
                
                # 创建一个覆盖图层
                overlay_layer = Image.new("RGBA", result.size, (0, 0, 0, 0))
                overlay_layer.paste(overlay_resized, (overlay_x, overlay_y), overlay_resized)
                
                # 提取覆盖图的RGB和透明度通道
                r, g, b, a = overlay_layer.split()
                
                # 提取结果图像的RGB和透明度通道
                r2, g2, b2, a2 = result.split()
                
                # 手动进行自定义的混合（正片叠底，但保持适当的透明度）
                # 对于每个颜色通道应用正片叠底效果，但调整透明度处理方式
                r3 = ImageChops.multiply(r, r2)
                g3 = ImageChops.multiply(g, g2)
                b3 = ImageChops.multiply(b, b2)
                
                # 透明度通道使用原始图像的透明度 
                # 这确保了没有黑边
                
                # 根据覆盖图的透明度权重来应用混合
                # 创建一个新的蒙版，表示应该应用正片叠底效果的地方
                # 255 表示完全应用，0 表示不应用
                blend_mask = Image.new("L", result.size, 0)
                blend_mask.paste(a, (0, 0), a)  # 使用覆盖图自身的alpha作为混合蒙版
                
                # 创建最终的RGB通道
                r_final = Image.blend(r2, r3, 0.7)  # 使用0.7作为系数可以减轻效果
                g_final = Image.blend(g2, g3, 0.7)
                b_final = Image.blend(b2, b3, 0.7)
                
                # 合并通道
                final_result = Image.merge("RGBA", (r_final, g_final, b_final, a2))
                
                if self.debug_mode:
                    print("使用自定义混合模式应用背景覆盖图")
                
                result = final_result
            
            # 添加顶层图片（放在最后，处于最顶层）
            if self.use_top_img.get() and 'top' in self.cached_images:
                top_img = self.cached_images['top'].copy()
                if self.debug_mode:
                    print("正在添加顶层图片")
                    print(f"顶层图片尺寸: {top_img.width}x{top_img.height}")
                
                # 创建顶层图层并粘贴
                top_layer = Image.new("RGBA", result.size, (0, 0, 0, 0))
                top_layer.paste(top_img, (0, 0), top_img)
                
                # 使用alpha合成添加顶层图片
                result = Image.alpha_composite(result, top_layer)
            elif self.debug_mode and self.use_top_img.get():
                print("顶层图片未在缓存中找到")
            
            return result
        
        except Exception as e:
            messagebox.showerror("处理错误", f"处理图片时出错: {str(e)}")
            if self.debug_mode:
                import traceback
                traceback.print_exc()
            return None
    
    def prev_image(self):
        """预览上一张图片"""
        if self.selected_images:
            self.current_image_index = (self.current_image_index - 1) % len(self.selected_images)
            self.update_preview()
    
    def next_image(self):
        """预览下一张图片"""
        if self.selected_images:
            self.current_image_index = (self.current_image_index + 1) % len(self.selected_images)
            self.update_preview()
    
    def batch_process(self):
        """批量处理并导出图片"""
        if 'base' not in self.cached_images or not self.selected_images:
            messagebox.showwarning("警告", "请先选择需要处理的图片")
            return
        
        output_dir = filedialog.askdirectory(title="选择保存目录")
        if not output_dir:
            return
        
        try:
            # 创建进度窗口
            progress_window = tk.Toplevel(self.root)
            progress_window.title("处理进度")
            progress_window.geometry("300x100")
            
            progress_label = ttk.Label(progress_window, text="正在处理图片...")
            progress_label.pack(pady=10)
            
            progress_bar = ttk.Progressbar(progress_window, orient=tk.HORIZONTAL, length=250, mode='determinate')
            progress_bar.pack(pady=10)
            
            total_images = len(self.selected_images)
            progress_bar['maximum'] = total_images
            
            for i, img_path in enumerate(self.selected_images):
                # 更新进度条
                progress_bar['value'] = i + 1
                progress_label.config(text=f"正在处理: {i+1}/{total_images}")
                progress_window.update()
                
                # 处理图片
                processed_img = self.process_image(img_path)
                
                # 保存图片
                if processed_img:
                    filename = os.path.basename(img_path)
                    output_path = os.path.join(output_dir, f"processed_{filename}")
                    processed_img.save(output_path)
            
            progress_window.destroy()
            messagebox.showinfo("完成", f"已成功处理并保存 {total_images} 张图片到 {output_dir}")
        
        except Exception as e:
            messagebox.showerror("错误", f"批量处理时出错: {str(e)}")
    
    def load_config(self):
        """加载配置文件"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                
                # 加载图片路径
                if 'base_img_path' in config and os.path.exists(config['base_img_path']):
                    self.base_img_path = config['base_img_path']
                if 'title_img_path' in config and os.path.exists(config['title_img_path']):
                    self.title_img_path = config['title_img_path']
                if 'overlay_img_path' in config and os.path.exists(config['overlay_img_path']):
                    self.overlay_img_path = config['overlay_img_path']
                if 'top_img_path' in config and os.path.exists(config['top_img_path']):
                    self.top_img_path = config['top_img_path']
                
                # 加载参数
                if 'scale_factor' in config:
                    self.scale_factor.set(config['scale_factor'])
                if 'x_offset' in config:
                    self.x_offset.set(config['x_offset'])
                if 'y_offset' in config:
                    self.y_offset.set(config['y_offset'])
                if 'overlay_scale_factor' in config:
                    self.overlay_scale_factor.set(config['overlay_scale_factor'])
                if 'crop_bottom_percent' in config:
                    self.crop_bottom_percent.set(config['crop_bottom_percent'])
                if 'crop_right_percent' in config:
                    self.crop_right_percent.set(config['crop_right_percent'])
                if 'crop_top_percent' in config:
                    self.crop_top_percent.set(config['crop_top_percent'])
                if 'crop_corner_size' in config:
                    self.crop_corner_size.set(config['crop_corner_size'])
                if 'use_corner_crop' in config:
                    self.use_corner_crop.set(config['use_corner_crop'])
                
                # 加载图层启用状态
                if 'use_base_img' in config:
                    self.use_base_img.set(config['use_base_img'])
                if 'use_title_img' in config:
                    self.use_title_img.set(config['use_title_img'])
                if 'use_overlay_img' in config:
                    self.use_overlay_img.set(config['use_overlay_img'])
                if 'use_top_img' in config:
                    self.use_top_img.set(config['use_top_img'])
                
                if self.debug_mode:
                    print("成功加载配置文件")
        
        except Exception as e:
            if self.debug_mode:
                print(f"加载配置文件时出错: {str(e)}")
    
    def save_config(self):
        """保存配置到文件"""
        try:
            config = {
                # 图片路径
                'base_img_path': self.base_img_path,
                'title_img_path': self.title_img_path,
                'overlay_img_path': self.overlay_img_path,
                'top_img_path': self.top_img_path,
                
                # 参数
                'scale_factor': self.scale_factor.get(),
                'x_offset': self.x_offset.get(),
                'y_offset': self.y_offset.get(),
                'overlay_scale_factor': self.overlay_scale_factor.get(),
                'crop_bottom_percent': self.crop_bottom_percent.get(),
                'crop_right_percent': self.crop_right_percent.get(),
                'crop_top_percent': self.crop_top_percent.get(),
                'crop_corner_size': self.crop_corner_size.get(),
                'use_corner_crop': self.use_corner_crop.get(),
                
                # 图层启用状态
                'use_base_img': self.use_base_img.get(),
                'use_title_img': self.use_title_img.get(),
                'use_overlay_img': self.use_overlay_img.get(),
                'use_top_img': self.use_top_img.get(),
            }
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=4)
            
            if self.debug_mode:
                print("成功保存配置文件")
        
        except Exception as e:
            if self.debug_mode:
                print(f"保存配置文件时出错: {str(e)}")
    
    def on_closing(self):
        """窗口关闭时的处理"""
        self.save_config()
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = EnglishPicProcessor(root)
    root.mainloop() 