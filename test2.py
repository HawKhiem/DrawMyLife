from manim import *
import itertools as it
import operator as op
import numpy as np
from functools import reduce

class FourierCirclesScene(ZoomedScene):
    def __init__(self, **kwargs):
        super().__init__(
            zoom_factor=0.3,
            zoomed_display_height=3,
            zoomed_display_width=4,
            image_frame_stroke_width=1,
            zoomed_camera_config={
                "default_frame_stroke_width": 3,
                "cairo_line_width_multiple": 0.05,
            },
            **kwargs
        )
        self.n_vectors = 10
        self.big_radius = 2
        self.colors = [
            BLUE_D,
            BLUE_C,
            BLUE_E,
            GREY_BROWN,
        ]
        self.vector_config = {
            "buff": 0,
            "max_tip_length_to_length_ratio": 0.25,
            "tip_length": 0.15,
            "max_stroke_width_to_length_ratio": 10,
            "stroke_width": 1.7,
        }
        self.circle_config = {
            "stroke_width": 1,
        }
        self.base_frequency = 1
        self.slow_factor = 0.5
        self.center_point = ORIGIN
        self.parametric_function_step_size = 0.001
        self.drawn_path_color = YELLOW
        self.drawn_path_stroke_width = 2
        self.interpolate_config = [0, 1]
        self.include_zoom_camera = False
        self.scale_zoom_camera_to_full_screen = False
        self.scale_zoom_camera_to_full_screen_at = 4
        self.wait_before_start = None

        self.slow_factor_tracker = ValueTracker(self.slow_factor)
        self.vector_clock = ValueTracker(0)
        self.add(self.vector_clock)

        # Initialize vectors as an empty VGroup
        self.vectors = VGroup()

    def setup(self):
        super().setup()
        self.add_vector_clock()

    def add_vector_clock(self):
        self.vector_clock.add_updater(
            lambda m, dt: m.increment_value(
                self.get_slow_factor() * dt
            )
        )

    def get_slow_factor(self):
        return self.slow_factor_tracker.get_value()

    def get_vector_time(self):
        return self.vector_clock.get_value()

    def get_freqs(self):
        n = self.n_vectors
        all_freqs = list(range(n // 2, -n // 2, -1))
        all_freqs.sort(key=abs)
        return all_freqs

    def get_coefficients(self):
        return [complex(0) for _ in range(self.n_vectors)]

    def get_color_iterator(self):
        return it.cycle(self.colors)

    def get_rotating_vectors(self, freqs=None, coefficients=None):
        vectors = VGroup()
        self.center_tracker = VectorizedPoint(self.center_point)

        if freqs is None:
            freqs = self.get_freqs()
        if coefficients is None:
            coefficients = self.get_coefficients()

        last_vector = None
        for freq, coefficient in zip(freqs, coefficients):
            if last_vector:
                center_func = last_vector.get_end
            else:
                center_func = self.center_tracker.get_location
            vector = self.get_rotating_vector(
                coefficient=coefficient,
                freq=freq,
                center_func=center_func,
            )
            vectors.add(vector)
            last_vector = vector
        self.vectors = vectors
        return vectors

    def get_rotating_vector(self, coefficient, freq, center_func):
        vector = Vector(RIGHT, **self.vector_config)
        vector.scale(abs(coefficient))
        if abs(coefficient) == 0:
            phase = 0
        else:
            phase = np.log(coefficient).imag
        vector.rotate(phase, about_point=ORIGIN)
        vector.freq = freq
        vector.coefficient = coefficient
        vector.center_func = center_func
        vector.add_updater(self.update_vector)
        return vector

    def update_vector(self, vector, dt):
        time = self.get_vector_time()
        coef = vector.coefficient
        freq = vector.freq
        phase = np.log(coef).imag

        vector.set_length(abs(coef))
        vector.set_angle(phase + time * freq * TAU)
        vector.shift(vector.center_func() - vector.get_start())
        return vector

    def get_circles(self, vectors):
        return VGroup(*[
            self.get_circle(
                vector,
                color=color
            )
            for vector, color in zip(
                vectors,
                self.get_color_iterator()
            )
        ])

    def get_circle(self, vector, color=BLUE):
        circle = Circle(color=color, **self.circle_config)
        circle.center_func = vector.get_start
        circle.radius_func = vector.get_length
        circle.add_updater(self.update_circle)
        return circle

    def update_circle(self, circle):
        circle.set_width(2 * circle.radius_func())
        circle.move_to(circle.center_func())
        return circle

    def get_vector_sum_path(self, vectors, color=YELLOW):
        coefs = [v.coefficient for v in vectors]
        freqs = [v.freq for v in vectors]
        center = vectors[0].get_start()

        path = ParametricFunction(
            lambda t: center + reduce(op.add, [
                complex_to_R3(
                    coef * np.exp(TAU * 1j * freq * t)
                )
                for coef, freq in zip(coefs, freqs)
            ]),
            t_min=0,
            t_max=1,
            color=color,
            step_size=self.parametric_function_step_size,
        )
        return path

    def get_drawn_path_alpha(self):
        return self.get_vector_time()

    def get_drawn_path(self, vectors, stroke_width=None, **kwargs):
        if stroke_width is None:
            stroke_width = self.drawn_path_stroke_width
        path = self.get_vector_sum_path(vectors, **kwargs)
        broken_path = CurvesAsSubmobjects(path)
        broken_path.curr_time = 0
        start, end = self.interpolate_config

        def update_path(path, dt):
            alpha = self.get_drawn_path_alpha()
            n_curves = len(path)
            for a, sp in zip(np.linspace(0, 1, n_curves), path):
                b = (alpha - a)
                if b < 0:
                    width = 0
                else:
                    width = stroke_width * interpolate(start, end, (1 - (b % 1)))
                sp.set_stroke(width=width)
            path.curr_time += dt
            return path

        broken_path.set_color(self.drawn_path_color)
        broken_path.add_updater(update_path)
        return broken_path

    def get_y_component_wave(self,
                             vectors,
                             left_x=1,
                             color=PINK,
                             n_copies=2,
                             right_shift_rate=5):
        path = self.get_vector_sum_path(vectors)
        wave = ParametricFunction(
            lambda t: op.add(
                right_shift_rate * t * LEFT,
                path.function(t)[1] * UP
            ),
            t_min=path.t_min,
            t_max=path.t_max,
            color=color,
        )
        wave_copies = VGroup(*[
            wave.copy()
            for x in range(n_copies)
        ])
        wave_copies.arrange(RIGHT, buff=0)
        top_point = wave_copies.get_top()
        wave_creation = Create(
            wave,
            run_time=(1 / self.get_slow_factor()),
            rate_func=linear,
        )
        self.play(wave_creation)
        wave.add_updater(lambda m: m.shift(
            (m.get_left()[0] - left_x) * LEFT
        ))

        def update_wave_copies(wcs):
            # Use the actual runtime elapsed to match the wave progress
            elapsed_time = wave_creation.run_time
            index = int(elapsed_time * self.camera.frame_rate)
            wcs[:index].match_style(wave)
            wcs[index:].set_stroke(width=0)
            wcs.next_to(wave, RIGHT, buff=0)
            wcs.align_to(top_point, UP)

        wave_copies.add_updater(update_wave_copies)

        return VGroup(wave, wave_copies)

    def get_wave_y_line(self, vectors, wave):
        return DashedLine(
            vectors[-1].get_end(),
            wave[0].get_end(),
            stroke_width=1,
            dash_length=DEFAULT_DASH_LENGTH * 0.5,
        )

    def get_coefficients_of_path(self, path, n_samples=10000, freqs=None):
        if freqs is None:
            freqs = self.get_freqs()
        dt = 1 / n_samples
        ts = np.arange(0, 1, dt)
        samples = np.array([
            path.point_from_proportion(t)
            for t in ts
        ])
        samples -= self.center_point
        complex_samples = samples[:, 0] + 1j * samples[:, 1]

        return [
            np.array([
                np.exp(-TAU * 1j * freq * t) * cs
                for t, cs in zip(ts, complex_samples)
            ]).sum() * dt for freq in freqs
        ]

    def zoom_config(self):
        self.activate_zooming(animate=False)
        self.zoomed_display.add_updater(lambda mob: mob.move_to(self.vectors[-1].get_end()))

    def scale_zoom_camera_to_full_screen_config(self):
        def fix_update(mob, dt, velocity_factor, dt_calculate):
            if dt == 0 and mob.counter == 0:
                rate = velocity_factor * dt_calculate
                mob.counter += 1
            else:
                rate = dt * velocity_factor
            if dt > 0:
                mob.counter = 0
            return rate

        fps = 1 / self.camera.frame_rate
        mob = self.zoomed_display
        mob.counter = 0
        velocity_factor = 1  # Default velocity factor for zoom animation
        mob.start_time = 0
        run_time = 3  # Default runtime for zoom animation
        run_time *= 2
        mob_height = mob.get_height()
        mob_width = mob.get_width()
        mob_center = mob.get_center()
        ctx = self.zoomed_camera.cairo_line_width_multiple

        def update_camera(mob, dt):
            line = Line(
                mob_center,
                self.camera.frame_center
            )
            mob.start_time += fix_update(mob, dt, velocity_factor, fps)
            if mob.start_time <= run_time:
                alpha = mob.start_time / run_time
                alpha_func = there_and_back_with_pause(alpha)
                coord = line.point_from_proportion(alpha_func)
                mob.set_height(
                    interpolate(
                        mob_height,
                        self.camera.frame_height,
                        alpha_func
                    ),
                    stretch=True
                )
                mob.set_width(
                    interpolate(
                        mob_width,
                        self.camera.frame_width,
                        alpha_func
                    ),
                    stretch=True
                )
                self.zoomed_camera.cairo_line_width_multiple = interpolate(
                    ctx,
                    self.camera.cairo_line_width_multiple,
                    alpha_func
                )
                mob.move_to(coord)
            return mob

        self.zoomed_display.add_updater(update_camera)

#################################
#################################


class CustomAnimationExample(FourierCirclesScene):
    def __init__(self, **kwargs):
        FourierCirclesScene.__init__(self, **kwargs)
        # Default configuration values
        self.n_vectors = 200
        self.slow_factor = 0.2
        self.fourier_symbol_config = {
            "stroke_width": 0,
            "fill_opacity": 0,
            "height": 4,
            "fill_color": WHITE
        }
        self.circle_config = {
            "stroke_width": 1,
            "stroke_opacity": 0.3,
        }

    def construct(self):
        # Create symbols
        t_symbol = Tex("T", **self.fourier_symbol_config)
        c_clef_symbol = SVGMobject("svg-image-7", **self.fourier_symbol_config)
        c_clef_symbol.match_height(t_symbol)

        # Set gradient and color for symbols
        for mob in [t_symbol, c_clef_symbol]:
            mob.set_sheen(0, UP)
            mob.set_color_by_gradient(BLACK, GRAY, WHITE)

        # Group symbols
        group = VGroup(t_symbol, c_clef_symbol).arrange(RIGHT, buff=0.1)

        # Get paths
        path1 = t_symbol.family_members_with_points()[0]
        path2 = c_clef_symbol.family_members_with_points()[0]

        # Get coefficients and vectors for paths
        coefs1 = self.get_coefficients_of_path(path1)
        vectors1 = self.get_rotating_vectors(coefficients=coefs1)
        circles1 = self.get_circles(vectors1, **self.circle_config)
        drawn_path1 = self.get_drawn_path(vectors1)

        coefs2 = self.get_coefficients_of_path(path2)
        vectors2 = self.get_rotating_vectors(coefficients=coefs2)
        circles2 = self.get_circles(vectors2, **self.circle_config)
        drawn_path2 = self.get_drawn_path(vectors2)

        # Define text
        text = Tex("Thanks for watching!")
        text.scale(1.5)
        text.next_to(group, DOWN)

        # Combine all elements
        all_mobs = VGroup(group, text)

        # Prepare elements to remove
        vectors1_to_fade = vectors1.copy()
        circles1_to_fade = circles1.copy()
        vectors1_to_fade.clear_updaters()
        circles1_to_fade.clear_updaters()

        vectors2_to_fade = vectors2.copy()
        circles2_to_fade = circles2.copy()
        vectors2_to_fade.clear_updaters()
        circles2_to_fade.clear_updaters()

        # Animation
        self.play(
            *[GrowArrow(arrow) for arrow in vectors1_to_fade],
            *[Create(circle) for circle in circles1_to_fade],
            *[GrowArrow(arrow) for arrow in vectors2_to_fade],
            *[Create(circle) for circle in circles2_to_fade],
            run_time=2.5,
        )

        self.remove(*vectors1_to_fade, *circles1_to_fade, *vectors2_to_fade, *circles2_to_fade)

        self.add(vectors1, circles1, drawn_path1.set_color(RED), vectors2, circles2, drawn_path2.set_color(BLUE))

        self.add_vector_clock()

        self.wait(1 / self.slow_factor)

        self.bring_to_back(t_symbol, c_clef_symbol)

        self.play(
            t_symbol.fade(1),
            c_clef_symbol.fade(1),
            run_time=3
        )

        self.wait()

        self.play(
            self.camera.frame.set_height, all_mobs.get_height() * 1.2,
            self.camera.frame.move_to, all_mobs.get_center()
        )

        self.wait(0.5)

        self.play(Write(text))

        self.wait(10)

    def get_coefficients_of_path(self, path, n_samples=10000):
        dt = 1 / n_samples
        ts = np.arange(0, 1, dt)
        samples = np.array([
            path.point_from_proportion(t)
            for t in ts
        ])
        samples -= path.point_from_proportion(0)
        complex_samples = samples[:, 0] + 1j * samples[:, 1]

        return [
            np.array([
                np.exp(-TAU * 1j * freq * t) * cs
                for t, cs in zip(ts, complex_samples)
            ]).sum() * dt for freq in range(-n_samples // 2, n_samples // 2)
        ]

    def get_rotating_vectors(self, coefficients):
        vectors = VGroup()
        last_vector = None
        for freq, coefficient in enumerate(coefficients):
            if last_vector:
                center_func = last_vector.get_end
            else:
                center_func = ORIGIN
            vector = Arrow(ORIGIN, UP)
            vector.scale(abs(coefficient))
            if abs(coefficient) != 0:
                phase = np.log(coefficient).imag
                vector.rotate(phase, about_point=ORIGIN)
            vector.freq = freq
            vector.coefficient = coefficient
            vector.center_func = center_func
            vector.add_updater(self.update_vector)
            vectors.add(vector)
            last_vector = vector
        return vectors

    def update_vector(self, vector, dt):
        time = self.get_vector_time()
        coef = vector.coefficient
        freq = vector.freq
        phase = np.log(coef).imag

        vector.set_length(abs(coef))
        vector.set_angle(phase + time * freq * TAU)
        vector.shift(vector.center_func() - vector.get_start())
        return vector

    def get_circles(self, vectors, stroke_width=None):
        if stroke_width is None:
            stroke_width = self.circle_config.get("stroke_width", 1)
        return VGroup(*[
            self.get_circle(
                vector,
                color=color
            )
            for vector, color in zip(
                vectors,
                self.get_color_iterator()
            )
        ])

    def get_drawn_path(self, vectors, color=YELLOW):
        path_points = np.array([
            vector.get_end()
            for vector in vectors
        ])
        path = VMobject()
        path.set_points_smoothly(path_points)
        path.set_color(color)
        return path

    def get_vector_time(self):
        return self.time * self.slow_factor if hasattr(self, "time") else 0



