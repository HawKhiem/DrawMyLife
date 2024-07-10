from manim import *
from MatNgocXit import mat_ngoc_points
from Phoi import phoi_points
from Lan1 import lan1_points
from Lan2 import lan2_points
from Lan3 import lan3_points
from Lan4 import lan4_points
from Lan5 import lan5_points
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
        self.n_vectors = 714
        self.cycle_seconds = 15
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
            lambda t, dt: t.increment_value(dt * min(1.0, 20 * self.slow_factor_tracker.get_value()) / self.cycle_seconds)
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
        self.n_cycles = 30
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

class FaceScene(FourierOfPiSymbol):
    def __init__(self):
        super().__init__()
        self.n_vectors = 101
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

class CircleSence(FourierOfPiSymbol):
    def __init__(self):
        super().__init__()
        self.n_vectors = 1001
        self.run_time = 30
        self.start_drawn = True
        self.file_name = "circle.svg"
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

class GuyScene(FourierSceneAbstract):
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
        symbol1 = self.get_tex_symbol("g", RED)
        symbol2 = self.get_tex_symbol("u", BLUE)
        symbol3 = self.get_tex_symbol("y", GREEN)
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


class DrawTwoSVG(FourierOfPiSymbol):
    def __init__(self):
        super().__init__()
        self.n_vectors = 101
        self.run_time = 30
        self.start_drawn = True
        self.file_name_1 = "left"
        self.file_name_2 = "right"
        self.height = 5


    def get_shape(self, file_name):
        shape = SVGMobject(file_name)
        return shape

    def get_path_from_shape(self, shape):
        path = shape.family_members_with_points()[0]
        path.set_fill(opacity=0)
        path.set_stroke(WHITE, 1)
        path.set_height(self.height)
        return path

    def construct(self):
        # Symbols to draw
        shape1 = self.get_shape(self.file_name_1)
        path1 = self.get_path_from_shape(shape1)

        shape2 = self.get_shape(self.file_name_2)
        path2 = self.get_path_from_shape(shape2)

        # Fourier series for shape1
        vectors1 = self.get_fourier_vectors(path1)
        circles1 = self.get_circles(vectors1)
        drawn_path1 = self.get_drawn_path(vectors1).set_color(RED)

        # Fourier series for shape2
        vectors2 = self.get_fourier_vectors(path2)
        circles2 = self.get_circles(vectors2)
        drawn_path2 = self.get_drawn_path(vectors2).set_color(BLUE)
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

class DrawTwo(FourierOfPiSymbol):
    def __init__(self):
        super().__init__()
        self.n_vectors = 101
        self.run_time = 30
        self.start_drawn = True
        self.height = 250

    def get_shape1(self):
        # Define the shape for the first path
        step_points = [
            (718, 319, 0),
            (708, 279, 0),
            (688, 244, 0),
            (657, 224, 0),
            (622, 215, 0),
            (568, 216, 0),
            (498, 229, 0),
            (444, 274, 0),
            (442, 321, 0),
            (452, 373, 0),
            (478, 433, 0),
            (504, 474, 0),
            (544, 519, 0),
            (591, 562, 0),
            (635, 603, 0),
            (670, 644, 0),
            (709, 688, 0),
        ]
        shape = VMobject()
        inverted_points = [[x, - y, z] for x, y, z in step_points]
        shape.set_points_as_corners([*inverted_points, inverted_points[0]])  # Close the loop
        return shape

    def get_shape2(self):
        # Define the shape for the second path
        step_points = [
            (724, 308, 0),
            (751, 267, 0),
            (787, 234, 0),
            (827, 220, 0),
            (867, 214, 0),
            (917, 227, 0),
            (945, 246, 0),
            (965, 271, 0),
            (980, 305, 0),
            (978, 354, 0),
            (963, 395, 0),
            (936, 436, 0),
            (906, 467, 0),
            (871, 492, 0),
            (840, 531, 0),
            (810, 562, 0),
            (769, 616, 0),
            (751, 647, 0),
            (731, 688, 0),
        ]
        shape = VMobject()
        inverted_points = [[x, -y, z] for x, y, z in step_points]
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
        path_center = path1.get_center()
        self.camera.frame.move_to(path_center)  # Center the frame around the shape's coordinates

        vectors1 = self.get_fourier_vectors(path1)
        circles1 = self.get_circles(vectors1)
        drawn_path1 = self.get_drawn_path(vectors1).set_color(YELLOW)

        vectors2 = self.get_fourier_vectors(path2)
        circles2 = self.get_circles(vectors2)
        drawn_path2 = self.get_drawn_path(vectors2).set_color(RED)

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

class DrawPhoi(FourierOfPiSymbol):
    def __init__(self):
        super().__init__()
        self.n_vectors = 101
        self.run_time = 30
        self.start_drawn = True

    def get_shape(self):
        # Define the shape for the step function

        shape = VMobject()
        inverted_points = [[x, -y, z] for x, y, z in phoi_points]
        shape.set_points_as_corners([*inverted_points, inverted_points[0]])  # Close the loop
        return shape

    def get_path(self):
        shape = self.get_shape()
        path = shape.family_members_with_points()[0]
        path.set_fill(opacity=0)
        path.set_stroke(WHITE, 0)
        return path

    def construct(self):
        # Adjust the camera frame
        self.camera.frame.set_width(self.get_path().width)
        self.camera.frame.set_height(self.get_path().height)
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


class DrawMatNgocXit(FourierOfPiSymbol):
    def __init__(self):
        super().__init__()
        self.n_vectors = 101
        self.run_time = 30
        self.start_drawn = True

    def get_shape(self):
        # Define the shape for the step function
        shape = VMobject()
        inverted_points = [[x, -y, z] for x, y, z in mat_ngoc_points]
        shape.set_points_as_corners([*inverted_points, inverted_points[0]])  # Close the loop
        return shape

    def get_path(self):
        shape = self.get_shape()
        path = shape.family_members_with_points()[0]
        path.set_fill(opacity=0)
        path.set_stroke(WHITE, 0)
        return path

    def construct(self):
        # Adjust the camera frame
        self.camera.frame.set_width(self.get_path().width)
        self.camera.frame.set_height(self.get_path().height)
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

class DrawLan1(FourierOfPiSymbol):
    def __init__(self):
        super().__init__()
        self.n_vectors = 101
        self.run_time = 30
        self.start_drawn = True

    def get_shape(self):
        # Define the shape for the step function
        shape = VMobject()
        inverted_points = [[x, -y, z] for x, y, z in lan1_points]
        shape.set_points_as_corners([*inverted_points, inverted_points[0]])  # Close the loop
        return shape

    def get_path(self):
        shape = self.get_shape()
        path = shape.family_members_with_points()[0]
        path.set_fill(opacity=0)
        path.set_stroke(WHITE, 0)
        return path

    def construct(self):
        # Adjust the camera frame
        self.camera.frame.set_width(self.get_path().width)
        self.camera.frame.set_height(self.get_path().height)
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
        self.play(self.slow_factor_tracker.animate.set_value(1), run_time= 4 * self.cycle_seconds)
        self.wait(1 * self.cycle_seconds)

class DrawLan2(FourierOfPiSymbol):
    def __init__(self):
        super().__init__()
        self.n_vectors = 101
        self.run_time = 30
        self.start_drawn = True

    def get_shape(self):
        shape = VMobject()
        inverted_points = [[x, -y, z] for x, y, z in lan2_points]
        shape.set_points_as_corners([*inverted_points, inverted_points[0]])  # Close the loop
        return shape

    def get_path(self):
        shape = self.get_shape()
        path = shape.family_members_with_points()[0]
        path.set_fill(opacity=0)
        path.set_stroke(WHITE, 0)
        return path

    def construct(self):
        # Adjust the camera frame
        self.camera.frame.set_width(self.get_path().width)
        self.camera.frame.set_height(self.get_path().height)
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
        self.play(self.slow_factor_tracker.animate.set_value(1), run_time= 4 * self.cycle_seconds)
        self.wait(1 * self.cycle_seconds)

class DrawLan3(FourierOfPiSymbol):
    def __init__(self):
        super().__init__()
        self.n_vectors = 101
        self.run_time = 30
        self.start_drawn = True

    def get_shape(self):
        # Define the shape for the step function
        shape = VMobject()
        inverted_points = [[x, -y, z] for x, y, z in lan3_points]
        shape.set_points_as_corners([*inverted_points, inverted_points[0]])  # Close the loop
        return shape

    def get_path(self):
        shape = self.get_shape()
        path = shape.family_members_with_points()[0]
        path.set_fill(opacity=0)
        path.set_stroke(WHITE, 0)
        return path

    def construct(self):
        # Adjust the camera frame
        self.camera.frame.set_width(self.get_path().width)
        self.camera.frame.set_height(self.get_path().height)
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
        self.play(self.slow_factor_tracker.animate.set_value(1), run_time= 4 * self.cycle_seconds)
        self.wait(1 * self.cycle_seconds)

class DrawLan4(FourierOfPiSymbol):
    def __init__(self):
        super().__init__()
        self.n_vectors = 101
        self.run_time = 30
        self.start_drawn = True

    def get_shape(self):
        shape = VMobject()
        inverted_points = [[x, -y, z] for x, y, z in lan4_points]
        shape.set_points_as_corners([*inverted_points, inverted_points[0]])  # Close the loop
        return shape

    def get_path(self):
        shape = self.get_shape()
        path = shape.family_members_with_points()[0]
        path.set_fill(opacity=0)
        path.set_stroke(WHITE, 0)
        return path

    def construct(self):
        # Adjust the camera frame
        self.camera.frame.set_width(self.get_path().width)
        self.camera.frame.set_height(self.get_path().height)
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
        self.play(self.slow_factor_tracker.animate.set_value(1), run_time= 4 * self.cycle_seconds)
        self.wait(1 * self.cycle_seconds)

class DrawLan5(FourierOfPiSymbol):
    def __init__(self):
        super().__init__()
        self.n_vectors = 101
        self.run_time = 30
        self.start_drawn = True

    def get_shape(self):
        shape = VMobject()
        inverted_points = [[x, -y, z] for x, y, z in lan5_points]
        shape.set_points_as_corners([*inverted_points, inverted_points[0]])  # Close the loop
        return shape

    def get_path(self):
        shape = self.get_shape()
        path = shape.family_members_with_points()[0]
        path.set_fill(opacity=0)
        path.set_stroke(WHITE, 0)
        return path

    def construct(self):
        # Adjust the camera frame
        self.camera.frame.set_width(self.get_path().width)
        self.camera.frame.set_height(self.get_path().height)
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
        self.play(self.slow_factor_tracker.animate.set_value(1), run_time= 4 * self.cycle_seconds)
        self.wait(1 * self.cycle_seconds)