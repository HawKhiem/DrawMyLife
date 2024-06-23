from manim import *
import numpy as np

class FourierSceneAbstract(ZoomedScene):
    def __init__(self):
        super().__init__()
        self.fourier_symbol_config = {
            "stroke_width": 100, # 100 folds
            "fill_opacity": 1,
            "height": 4,
        }
        self.vector_config = {
            "buff": 0,
            "max_tip_length_to_length_ratio": 0.25,
            "tip_length": 0.15,
            "max_stroke_width_to_length_ratio": 10,
            "stroke_width": 140 # 100 folds
        }
        self.circle_config = {
            "stroke_width": 100, # 100 folds
            "stroke_opacity": 0.3,
            "color": WHITE
        }
        self.n_vectors = 101
        self.cycle_seconds = 10
        self.parametric_func_step = 0.001
        self.drawn_path_stroke_width = 500 #100 folds
        self.drawn_path_interpolation_config = [0, 1]
        self.path_n_samples = 1000
        self.freqs = list(range(-self.n_vectors // 2, self.n_vectors // 2 + 1, 1))
        self.freqs.sort(key=abs)

    def setup(self):
        super().setup()
        self.vector_clock = ValueTracker()
        self.slow_factor_tracker = ValueTracker(0)
        self.add(self.vector_clock)

    def start_vector_clock(self):  # This updates vector_clock to follow the add_updater parameter dt
        self.vector_clock.add_updater(
            lambda t, dt: t.increment_value(dt * self.slow_factor_tracker.get_value() / self.cycle_seconds)
        )

    def stop_vector_clock(self):
        self.vector_clock.remove_updater(self.start_vector_clock)

    def get_fourier_coefs(self, path):
        dt = 1 / self.path_n_samples
        t_range = np.arange(0, 1, dt)

        points = np.array([
            path.point_from_proportion(t)
            for t in t_range
        ])
        complex_points = points[:, 0] + 1j * points[:, 1]

        coefficients = [
            np.sum(np.array([
                c_point * np.exp(-TAU * 1j * freq * t) * dt
                for t, c_point in zip(t_range, complex_points)
            ]))
            for freq in self.freqs
        ]
        return coefficients

    def get_fourier_vectors(self, path):
        coefficients = self.get_fourier_coefs(path)

        vectors = VGroup()
        v_is_first_vector = True
        for coef, freq in zip(coefficients, self.freqs):
            v = Vector([np.real(coef), np.imag(coef)], **self.vector_config)
            if v_is_first_vector:
                center_func = VectorizedPoint(ORIGIN).get_location  # Function to center position at tip of last vector
                v_is_first_vector = False
            else:
                center_func = last_v.get_end
            v.center_func = center_func
            last_v = v
            v.freq = freq
            v.coef = coef
            v.phase = np.angle(coef)
            v.shift(v.center_func() - v.get_start())
            v.set_angle(v.phase)
            vectors.add(v)
        return vectors

    def update_vectors(self, vectors):
        for v in vectors:
            time = self.vector_clock.get_value()
            v.shift(v.center_func() - v.get_start())
            v.set_angle(
                v.phase + time * v.freq * TAU)  # NOTE Rotate() did not work here for unknown reason, probably related to how manin handles updaters

    def get_circles(self, vectors):
        circles = VGroup()
        for v in vectors:
            c = Circle(radius=v.get_length(), **self.circle_config)
            c.center_func = v.get_start
            c.move_to(c.center_func())
            circles.add(c)
        return circles

    def update_circles(self, circles):
        for c in circles:
            c.move_to(c.center_func())

    def get_drawn_path(self, vectors):

        def fourier_series_func(t):
            fss = np.sum(np.array([
                v.coef * np.exp(TAU * 1j * v.freq * t)
                for v in vectors
            ]))
            real_fss = np.array([np.real(fss), np.imag(fss), 0])
            return real_fss

        t_range = np.array([0, 1, self.parametric_func_step])
        vector_sum_path = ParametricFunction(fourier_series_func, t_range=t_range)
        broken_path = CurvesAsSubmobjects(vector_sum_path)
        broken_path.stroke_width = 0
        broken_path.start_width = self.drawn_path_interpolation_config[0]
        broken_path.end_width = self.drawn_path_interpolation_config[1]
        return broken_path

    def update_path(self, broken_path):
        alpha = self.vector_clock.get_value()
        n_curves = len(broken_path)
        alpha_range = np.linspace(0, 1, n_curves)
        for a, subpath in zip(alpha_range, broken_path):
            b = (alpha - a)
            if b < 0:
                width = 0
            else:
                width = self.drawn_path_stroke_width * interpolate(broken_path.start_width, broken_path.end_width,
                                                                   (1 - (b % 1)))
            subpath.set_stroke(width=width)

class FourierOfPiSymbol(FourierSceneAbstract):
    def __init__(self):
        super().__init__()
        self.n_vectors = 101
        self.center_point = ORIGIN
        self.slow_factor = 0.1
        self.n_cycles = 1
        self.tex = "\\pi"
        self.start_drawn = False
        self.max_circle_stroke_width = 1

    def construct(self):
        vectors1 = self.get_fourier_vectors(self.get_path())
        circles1 = self.get_circles(vectors1)
        drawn_path1 = self.get_drawn_path(vectors1).set_color(RED)
        last_vector = vectors1[-1]

        def follow_end_vector(camera):
            camera.move_to(last_vector.get_end())
        self.wait(1)
        self.play(
            *[
                GrowArrow(arrow)
                for vector_group in [vectors1]
                for arrow in vector_group
            ],
            *[
                Create(circle)
                for circle_group in [circles1]
                for circle in circle_group
            ],
            run_time=3,
        )


        self.add(
            vectors1,
            circles1,
            drawn_path1.set_stroke(width = 0),
        )
        self.camera.frame.add_updater(follow_end_vector)
        vectors1.add_updater(self.update_vectors)
        circles1.add_updater(self.update_circles)
        drawn_path1.add_updater(self.update_path)
        self.start_vector_clock()
        self.play(self.slow_factor_tracker.animate.set_value(1), run_time=1 * self.cycle_seconds)
        self.wait(1 * self.cycle_seconds)


    def get_path(self):
        tex_mob = MathTex(self.tex)
        tex_mob.set_height(6)
        path = tex_mob.family_members_with_points()[0]
        path.set_fill(opacity=0)
        path.set_stroke(WHITE, 1)
        return path

class DrawTwoSVG(FourierOfPiSymbol):
    def __init__(self):
        super().__init__()
        self.n_vectors = 101
        self.run_time = 30
        self.start_drawn = True
        self.file_name_1 = "mouth"
        self.file_name_2 = "cat_face"
        # self.target_coords1 = np.array([-3.8385, 15.08, 0])
        # self.target_coords2 = np.array([36.20, 79.05, 0])


    def get_shape(self, file_name):
        shape = SVGMobject(file_name)
        return shape

    def get_path_from_shape(self, shape):
        path = shape.family_members_with_points()[0]
        path.set_fill(opacity=0)
        path.set_stroke(WHITE, 1)
        return path

    def construct(self):
        # newly added
        # self.camera.frame.set_width(1536)
        # self.camera.frame.set_height(864)
        # self.camera.frame.move_to([1536 / 2, 864 / 2, 0])  # Center the frame
        # newly added

        # Symbols to draw
        shape1 = self.get_shape(self.file_name_1)
        path1 = self.get_path_from_shape(shape1)

        # Newly added
        # current_center = path1.get_center()
        # shift_vector1 = self.target_coords1 - current_center
        # path1.shift(shift_vector1)
        # Newly added

        shape2 = self.get_shape(self.file_name_2)
        path2 = self.get_path_from_shape(shape2)
        # Newly added
        # current_center = path2.get_center()
        # shift_vector2 = self.target_coords2 - current_center
        # path2.shift(shift_vector2)
        # Newly added
        # group = VGroup(symbol1, symbol2, symbol3).arrange(RIGHT)



        # Fourier series for shape1
        vectors1 = self.get_fourier_vectors(path1)
        circles1 = self.get_circles(vectors1)
        drawn_path1 = self.get_drawn_path(vectors1).set_color(RED)
        drawn_path1.set_height(1)

        # Fourier series for shape2
        vectors2 = self.get_fourier_vectors(path2)
        circles2 = self.get_circles(vectors2)
        drawn_path2 = self.get_drawn_path(vectors2).set_color(BLUE)
        drawn_path2.set_height(10)
        # Camera updater
        last_vector = vectors1[-1]

        def follow_end_vector(camera):
            camera.move_to(last_vector.get_end())

        # Scene start
        self.wait(1)
        self.play(
            *[
                GrowArrow(arrow)
                for vector_group in [vectors1, vectors2]
                for arrow in vector_group
            ],
            run_time=3,
        )

        # Add objects to scene
        self.add(
            vectors1,
            drawn_path1.set_stroke(width=0),
            vectors2,
            drawn_path2.set_stroke(width=0),
        )
        # Add updaters and start vector clock
        self.camera.frame.add_updater(follow_end_vector)
        vectors1.add_updater(self.update_vectors)
        circles1.add_updater(self.update_circles)
        vectors2.add_updater(self.update_vectors)
        circles2.add_updater(self.update_circles)
        drawn_path1.add_updater(self.update_path)
        drawn_path2.add_updater(self.update_path)
        self.start_vector_clock()

        self.play(self.slow_factor_tracker.animate.set_value(1), run_time=0.5 * self.cycle_seconds)
        self.wait(1 * self.cycle_seconds)

class FourierOfTrebleClef(FourierOfPiSymbol):
    def __init__(self):
        super().__init__()
        self.n_vectors = 1001
        self.run_time = 30
        self.start_drawn = True
        self.file_name = "face"
        self.height = 5

    def get_shape(self):
        shape = SVGMobject(self.file_name)
        return shape

    def get_path(self):
        shape = self.get_shape()
        path = shape.family_members_with_points()[0]
        path.set_height(self.height)
        path.set_fill(opacity=0)
        path.set_stroke(WHITE, 0)
        return path

class FourierOfTrebleClef2(FourierOfPiSymbol):
    def __init__(self):
        super().__init__()
        self.n_vectors = 101
        self.run_time = 30
        self.start_drawn = True
        self.file_name = "cat"  # Ensure the SVG file is in the appropriate directory

    def get_shape(self):
        shape = SVGMobject(self.file_name)
        # shape.move_to(np.array([2, 2, 0]))  # Move the shape to specific coordinates
        return shape

    def get_path(self):
        shape = self.get_shape()
        path = shape.family_members_with_points()[0]

        # Get the first point of the path
        first_point = path.get_start()

        # Move the path to the first point
        path.move_to(first_point)

        path.set_fill(opacity=0)
        path.set_stroke(WHITE, 1)
        return path


class FourierOfTrebleClef3(FourierOfPiSymbol):
    def __init__(self):
        super().__init__()
        self.n_vectors = 101
        self.run_time = 30
        self.start_drawn = True
        self.file_name = "first"
        self.height = 30

    def get_shape(self):
        shape = SVGMobject(self.file_name)
        return shape

    def get_path(self):
        shape = self.get_shape()
        path = shape.family_members_with_points()[0]
        path.set_height(self.height)
        path.set_fill(opacity=0)
        path.set_stroke(WHITE, 0)
        path2 = path.get_end_anchors()
        xy_data = path2[0:len(path2) - 1, 0:2]
        return xy_data

class FourierScene(FourierSceneAbstract):
    def __init__(self):
        super().__init__()

    def get_tex_symbol(self, symbol, color=None):
        symbol = Tex(symbol, **self.fourier_symbol_config)

        if (color is not None):
            symbol.set_color(color)

        return symbol

    def get_path_from_symbol(self, symbol):
        return symbol.family_members_with_points()[0]

    def construct(self):
        # Symbols to draw
        symbol1 = self.get_tex_symbol("y", RED)
        symbol2 = self.get_tex_symbol("e", BLUE)
        symbol3 = self.get_tex_symbol("s", GREEN)
        group = VGroup(symbol1, symbol2, symbol3).arrange(RIGHT)

        # Fourier series for symbol1
        vectors1 = self.get_fourier_vectors(self.get_path_from_symbol(symbol1))
        circles1 = self.get_circles(vectors1)
        drawn_path1 = self.get_drawn_path(vectors1).set_color(RED)

        # Fourier series for symbol2
        vectors2 = self.get_fourier_vectors(self.get_path_from_symbol(symbol2))
        circles2 = self.get_circles(vectors2)
        drawn_path2 = self.get_drawn_path(vectors2).set_color(BLUE)

        # Fourier series for symbol3
        vectors3 = self.get_fourier_vectors(self.get_path_from_symbol(symbol3))
        circles3 = self.get_circles(vectors3)
        drawn_path3 = self.get_drawn_path(vectors3).set_color(GREEN)

        # Camera updater
        last_vector = vectors1[-1]

        def follow_end_vector(camera):
            camera.move_to(last_vector.get_end())

        # Scene start
        self.wait(1)
        self.play(
            *[
                GrowArrow(arrow)
                for vector_group in [vectors1, vectors2, vectors3]
                for arrow in vector_group
            ],
            run_time=3,
        )

        # Add objects to scene
        self.add(
            vectors1,
            drawn_path1.set_stroke(width=0),
            vectors2,
            drawn_path2.set_stroke(width=0),
            vectors3,
            drawn_path3.set_stroke(width=0),
        )
        # Add updaters and start vector clock
        self.camera.frame.add_updater(follow_end_vector)
        vectors1.add_updater(self.update_vectors)
        circles1.add_updater(self.update_circles)
        vectors2.add_updater(self.update_vectors)
        circles2.add_updater(self.update_circles)
        vectors3.add_updater(self.update_vectors)
        circles3.add_updater(self.update_circles)
        drawn_path1.add_updater(self.update_path)
        drawn_path2.add_updater(self.update_path)
        drawn_path3.add_updater(self.update_path)
        self.start_vector_clock()

        self.play(self.slow_factor_tracker.animate.set_value(1), run_time=0.5 * self.cycle_seconds)
        self.wait(1 * self.cycle_seconds)


class RandomFunction(FourierOfPiSymbol):
    def __init__(self):
        super().__init__()
        self.n_vectors = 101
        self.run_time = 30
        self.start_drawn = True
        self.height = 250

    def get_shape(self):
        # Define the shape for the step function
        step_points = [
            [193, 47, 0],
            [140, 204, 0],
            [123, 193, 0],
            [99, 189, 0],
            [74, 196, 0],
            [58, 213, 0],
            [49, 237, 0],
            [52, 261, 0],
            [65, 279, 0],
            [86, 292, 0],
            [113, 295, 0],
            [135, 282, 0],
            [152, 258, 0],
            [201, 95, 0],
            [212, 127, 0],
            [218, 150, 0],
            [213, 168, 0],
            [201, 185, 0],
            [192, 200, 0],
            [203, 214, 0],
            [219, 205, 0],
            [233, 191, 0],
            [242, 170, 0],
            [244, 149, 0],
            [242, 131, 0],
            [233, 111, 0]
        ]
        shape = VMobject()
        inverted_points = [[x, 250 - y, z] for x, y, z in step_points]
        shape.set_points_as_corners([*inverted_points, inverted_points[0]])  # Close the loop
        return shape

    def get_path(self):
        shape = self.get_shape()
        path = shape.family_members_with_points()[0]
        path.set_height(self.height)
        path.set_fill(opacity=0)
        path.set_stroke(WHITE, 0)
        return path

    def construct(self):
        # Adjust the camera frame
        self.camera.frame.set_width(300)
        self.camera.frame.set_height(300)
        path = self.get_path()
        path_center = path.get_center()
        self.camera.frame.move_to(path_center)  # Center the frame around the shape's coordinates
        vectors = self.get_fourier_vectors(path)
        circles = self.get_circles(vectors)
        drawn_path = self.get_drawn_path(vectors).set_color(YELLOW)
        last_vector = vectors[-1]

        def follow_end_vector(camera):
            camera.move_to(last_vector.get_end())

        self.wait(1)
        self.play(
            *[
                GrowArrow(arrow)
                for arrow in vectors[1:]  # Exclude the first vector
            ],
            *[
                Create(circle)
                for circle in circles[1:]  # Exclude the first circle
            ],
            run_time=3,
        )
        self.add(
            vectors,
            circles,
            vectors[0].set_stroke(width=0),  # Add vectors excluding the first
            circles[0].set_stroke(width=0),  # Add circles excluding the first
            drawn_path.set_stroke(width=0)
        )
        self.camera.frame.add_updater(follow_end_vector)
        vectors.add_updater(self.update_vectors)
        circles.add_updater(self.update_circles)
        drawn_path.add_updater(self.update_path)
        self.start_vector_clock()
        self.play(self.slow_factor_tracker.animate.set_value(1), run_time=1 * self.cycle_seconds)
        self.wait(1 * self.cycle_seconds)

class RandomFunction2(FourierOfPiSymbol):
    def __init__(self):
        super().__init__()
        self.n_vectors = 101
        self.run_time = 30
        self.start_drawn = True
        self.height = 250

    def get_shape(self):
        # Define the shape for the step function
        step_points = [
            [15, 365,0],
            [51, 336,0],
            [79, 309,0],
            [103, 285,0],
            [138, 261,0],
            [151, 256,0],
            [166, 253,0],
            [183, 255,0],
            [173, 248,0],
            [165, 245,0],
            [154, 244,0],
            [145, 238,0],
            [135, 231,0],
            [125, 218,0],
            [121, 203,0],
            [120, 185,0],
            [126, 178,0],
            [139, 164,0],
            [146, 154,0],
            [148, 146,0],
            [147, 124,0],
            [149, 107,0],
            [150, 90,0],
            [156, 74,0],
            [162, 64,0],
            [169, 57,0],
            [183, 50,0],
            [202, 41,0],
            [214, 39,0],
            [234, 34,0],
            [252, 32,0],
            [268, 31,0],
            [289, 38,0],
            [303, 52,0],
            [313, 63,0],
            [319, 78,0],
            [319, 90,0],
            [317, 103,0],
            [321, 115,0],
            [327, 128,0],
            [334, 135,0],
            [331, 146,0],
            [333, 156,0],
            [334, 162,0],
            [338, 173,0],
            [340, 188,0],
            [337, 198,0],
            [324, 202,0],
            [322, 211,0],
            [319, 221,0],
            [312, 227,0],
            [303, 231,0],
            [302, 238,0],
            [308, 245,0],
            [323, 248,0],
            [342, 255,0],
            [360, 258,0],
            [378, 261,0],
            [400, 267,0],
            [420, 279,0],
            [433, 296,0],
            [447, 321,0],
            [455, 347,0],
            [465, 362,0],
            [477, 378,0],
        ]
        shape = VMobject()
        inverted_points = [[x, 250 - y, z] for x, y, z in step_points]
        shape.set_points_as_corners([*inverted_points, inverted_points[0]])  # Close the loop
        return shape

    def get_path(self):
        shape = self.get_shape()
        path = shape.family_members_with_points()[0]
        path.set_height(self.height)
        path.set_fill(opacity=0)
        path.set_stroke(WHITE, 0)
        return path

    def construct(self):
        # Adjust the camera frame
        self.camera.frame.set_width(300)
        self.camera.frame.set_height(300)
        path = self.get_path()
        path_center = path.get_center()
        self.camera.frame.move_to(path_center)  # Center the frame around the shape's coordinates
        vectors = self.get_fourier_vectors(path)
        circles = self.get_circles(vectors)
        drawn_path = self.get_drawn_path(vectors).set_color(YELLOW)
        last_vector = vectors[-1]

        def follow_end_vector(camera):
            camera.move_to(last_vector.get_end())

        self.wait(1)
        self.play(
            *[
                GrowArrow(arrow)
                for arrow in vectors[1:]  # Exclude the first vector
            ],
            *[
                Create(circle)
                for circle in circles[1:]  # Exclude the first circle
            ],
            run_time=3,
        )
        self.add(
            vectors,
            circles,
            vectors[0].set_stroke(width=0),  # Add vectors excluding the first
            circles[0].set_stroke(width=0),  # Add circles excluding the first
            drawn_path.set_stroke(width=0)
        )
        self.camera.frame.add_updater(follow_end_vector)
        vectors.add_updater(self.update_vectors)
        circles.add_updater(self.update_circles)
        drawn_path.add_updater(self.update_path)
        self.start_vector_clock()
        self.play(self.slow_factor_tracker.animate.set_value(1), run_time=1 * self.cycle_seconds)
        self.wait(1 * self.cycle_seconds)

class StepFunction(FourierOfPiSymbol):
    def __init__(self):
        super().__init__()
        self.n_vectors = 101
        self.run_time = 30
        self.start_drawn = True
        self.height = 5

    def get_shape(self):
        # Define the shape for the step function
        step_points = [
            [-1, -1, 0], [-0.5, -1, 0], [-0.5, 1, 0], [0.5, 1, 0], [0.5, -1, 0], [1, -1, 0]
        ]
        shape = VMobject()
        shape.set_points_as_corners([*step_points, step_points[0]])  # Close the loop
        return shape

    def get_path(self):
        shape = self.get_shape()
        path = shape.family_members_with_points()[0]
        path.set_height(self.height)
        path.set_fill(opacity=0)
        path.set_stroke(WHITE, 0)
        return path

class RandomFunction3(FourierOfPiSymbol):
    def __init__(self):
        super().__init__()
        self.n_vectors = 101
        self.run_time = 30
        self.start_drawn = True
        self.height = 250

    def get_shape1(self):
        # Define the shape for the first path
        step_points = [
            (81, 17, 0),
            (76, 26, 0),
            (73, 33, 0),
            (71, 42, 0),
            (68, 52, 0),
            (67, 63, 0),
            (66, 71, 0),
            (64, 82, 0),
            (63, 92, 0),
            (62, 103, 0),
            (62, 112, 0),
            (61, 122, 0),
            (63, 134, 0),
            (68, 145, 0),
            (69, 158, 0),
            (67, 167, 0),
            (65, 177, 0),
            (61, 190, 0),
            (57, 197, 0),
            (52, 210, 0),
            (51, 221, 0),
            (51, 233, 0),
            (48, 245, 0),
            (49, 256, 0),
            (50, 267, 0),
            (50, 277, 0),
            (52, 291, 0),
            (51, 305, 0),
            (56, 315, 0),
            (60, 323, 0),
            (64, 334, 0),
            (70, 344, 0),
            (75, 354, 0),
            (82, 364, 0),
            (88, 374, 0),
            (92, 384, 0),
            (99, 393, 0),
            (106, 403, 0),
            (113, 413, 0),
            (121, 423, 0),
            (129, 433, 0),
            (135, 441, 0),
            (145, 451, 0),
            (156, 462, 0),
            (165, 468, 0),
            (175, 473, 0),
            (185, 479, 0),
            (195, 484, 0),
            (205, 490, 0),
            (217, 492, 0),
            (229, 495, 0),
            (242, 499, 0),
            (254, 502, 0),
            (267, 504, 0),
            (280, 504, 0),
            (292, 504, 0),
            (303, 504, 0),
            (313, 505, 0),
            (325, 505, 0),
            (337, 506, 0),
            (347, 505, 0),
            (357, 503, 0),
            (365, 500, 0),
            (375, 495, 0),
            (385, 489, 0),
            (393, 481, 0),
            (399, 474, 0),
            (406, 470, 0),
            (413, 461, 0),
            (419, 453, 0),
            (424, 446, 0),
            (430, 436, 0),
            (435, 429, 0),
            (439, 422, 0),
            (443, 416, 0),
            (449, 407, 0),
            (451, 399, 0),
            (457, 391, 0),
            (459, 385, 0),
            (464, 377, 0),
            (467, 368, 0),
            (470, 357, 0),
            (473, 347, 0),
            (475, 338, 0),
            (477, 329, 0),
            (478, 320, 0),
            (478, 310, 0),
            (479, 300, 0),
            (479, 292, 0),
            (478, 282, 0),
            (479, 272, 0),
            (475, 261, 0),
            (476, 251, 0),
            (473, 238, 0),
            (468, 227, 0),
            (463, 218, 0),
            (459, 212, 0),
            (453, 205, 0),
            (447, 201, 0),
            (440, 194, 0),
            (436, 188, 0),
            (435, 179, 0),
            (438, 171, 0),
            (440, 160, 0),
            (445, 150, 0),
            (449, 142, 0),
            (453, 133, 0),
            (454, 123, 0),
            (458, 114, 0),
            (460, 108, 0),
            (463, 98, 0),
            (466, 90, 0),
            (468, 79, 0),
            (470, 68, 0),
            (471, 63, 0),
            (472, 52, 0),
            (473, 40, 0),
            (474, 28, 0),
            (474, 17, 0),
            (469, 14, 0),
            (459, 15, 0),
            (452, 22, 0),
            (445, 28, 0),
            (438, 37, 0),
            (432, 44, 0),
            (425, 52, 0),
            (420, 59, 0),
            (417, 66, 0),
            (411, 73, 0),
            (403, 80, 0),
            (398, 86, 0),
            (388, 96, 0),
            (380, 103, 0),
            (374, 112, 0),
            (363, 122, 0),
            (356, 131, 0),
            (349, 138, 0),
            (342, 145, 0),
            (335, 153, 0),
            (325, 159, 0),
            (312, 160, 0),
            (300, 156, 0),
            (288, 153, 0),
            (277, 152, 0),
            (265, 151, 0),
            (254, 147, 0),
            (241, 145, 0),
            (232, 144, 0),
            (221, 143, 0),
            (212, 142, 0),
            (200, 143, 0),
            (193, 145, 0),
            (184, 137, 0),
            (174, 126, 0),
            (169, 118, 0),
            (163, 109, 0),
            (158, 102, 0),
            (152, 93, 0),
            (147, 84, 0),
            (142, 77, 0),
            (131, 69, 0),
            (123, 59, 0),
            (114, 53, 0),
            (106, 46, 0),
            (97, 37, 0),
            (90, 31, 0),
            (85, 22, 0),
        ]
        shape = VMobject()
        inverted_points = [[x, 250 - y, z] for x, y, z in step_points]
        shape.set_points_as_corners([*inverted_points, inverted_points[0]])  # Close the loop
        return shape

    def get_shape2(self):
        # Define the shape for the second path
        step_points = [
            (200, 385, 0),
            (203, 394, 0),
            (206, 404, 0),
            (208, 415, 0),
            (214, 424, 0),
            (220, 432, 0),
            (228, 437, 0),
            (239, 439, 0),
            (247, 433, 0),
            (252, 423, 0),
            (256, 416, 0),
            (256, 406, 0),
            (257, 395, 0),
            (259, 388, 0),
            (263, 382, 0),
            (267, 388, 0),
            (268, 398, 0),
            (271, 407, 0),
            (273, 415, 0),
            (277, 421, 0),
            (280, 428, 0),
            (286, 432, 0),
            (293, 436, 0),
            (304, 439, 0),
            (311, 440, 0),
            (321, 440, 0),
            (334, 440, 0),
            (343, 435, 0),
            (348, 427, 0),
            (352, 420, 0),
            (356, 412, 0),
            (358, 400, 0),
            (360, 393, 0),
            (360, 385, 0),
            (356, 389, 0),
            (354, 398, 0),
            (351, 406, 0),
            (345, 416, 0),
            (340, 423, 0),
            (335, 428, 0),
            (327, 431, 0),
            (317, 432, 0),
            (309, 431, 0),
            (300, 430, 0),
            (293, 427, 0),
            (286, 422, 0),
            (281, 414, 0),
            (279, 403, 0),
            (275, 391, 0),
            (272, 383, 0),
            (264, 377, 0),
            (256, 380, 0),
            (254, 387, 0),
            (251, 396, 0),
            (251, 405, 0),
            (251, 411, 0),
            (249, 418, 0),
            (245, 426, 0),
            (239, 432, 0),
            (230, 432, 0),
            (226, 428, 0),
            (221, 423, 0),
            (216, 414, 0),
            (215, 407, 0),
            (211, 397, 0),
            (208, 392, 0),
            (203, 385, 0),
        ]
        shape = VMobject()
        inverted_points = [[x, 250 - y, z] for x, y, z in step_points]
        shape.set_points_as_corners([*inverted_points, inverted_points[0]])  # Close the loop
        return shape

    def get_path1(self):
        shape1 = self.get_shape1()
        path = shape1.family_members_with_points()[0]
        # path.set_height(self.height)
        path.set_fill(opacity=0)
        path.set_stroke(WHITE, 0)
        return path

    def get_path2(self):
        shape = self.get_shape2()
        path = shape.family_members_with_points()[0]
        # path.set_height(self.height)
        path.set_fill(opacity=0)
        path.set_stroke(WHITE, 0)
        return path

    def construct(self):
        # Adjust the camera frame
        self.camera.frame.set_width(self.get_path1().width)
        self.camera.frame.set_height(self.get_path1().height)

        path1 = self.get_path1()
        path2 = self.get_path2()


        # Normalize the paths to have the same height
        # path1_height = path1.get_height()
        # path2_height = path2.get_height()
        #
        # if path1_height != path2_height:
        #     scale_factor = path1_height / path2_height
        #     path2.scale(scale_factor)
        #
        #
        # path1_center = path1.get_center()
        # path2_center = path2.get_center()

        path_center = path1.get_center()
        self.camera.frame.move_to(path_center)  # Center the frame around the shape's coordinates

        vectors1 = self.get_fourier_vectors(path1)
        circles1 = self.get_circles(vectors1)
        drawn_path1 = self.get_drawn_path(vectors1).set_color(YELLOW)

        vectors2 = self.get_fourier_vectors(path2)
        circles2 = self.get_circles(vectors2)
        drawn_path2 = self.get_drawn_path(vectors2).set_color(BLUE)

        last_vector = vectors1[-1]

        def follow_end_vector(camera):
            camera.move_to(last_vector.get_end())

        self.wait(1)
        self.play(
            *[
                GrowArrow(arrow)
                for vector_group in [vectors1[1:], vectors2[1:]]  # Exclude the first vector
                for arrow in vector_group
            ],
            *[
                Create(circle)
                for circle_group in [circles1[1:], circles2[1:]]  # Exclude the first circle
                for circle in circle_group
            ],
            run_time=3,
        )

        self.add(
            vectors1,
            circles1,
            vectors2,
            circles2,
            vectors1[0].set_stroke(width=0),  # Add vectors excluding the first
            circles1[0].set_stroke(width=0),  # Add circles excluding the first
            vectors2[0].set_stroke(width=0),  # Add vectors excluding the first
            circles2[0].set_stroke(width=0),  # Add circles excluding the first
            drawn_path1.set_stroke(width=0),
            drawn_path2.set_stroke(width=0)
        )

        self.camera.frame.add_updater(follow_end_vector)
        vectors1.add_updater(self.update_vectors)
        circles1.add_updater(self.update_circles)
        drawn_path1.add_updater(self.update_path)
        vectors2.add_updater(self.update_vectors)
        circles2.add_updater(self.update_circles)
        drawn_path2.add_updater(self.update_path)
        self.start_vector_clock()
        self.play(self.slow_factor_tracker.animate.set_value(1), run_time=1 * self.cycle_seconds)
        self.wait(1 * self.cycle_seconds)

