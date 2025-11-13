"""
Human Behavior Simulation

Simulates realistic human interactions:
- Mouse movements with bezier curves
- Natural scrolling patterns
- Random pauses and hesitations
- Realistic reading behavior
"""

import random
import time
import math
from typing import Tuple, List, Optional
from playwright.sync_api import Page, Locator
import numpy as np


class HumanBehaviorSimulator:
    """Simulate human-like browser interactions"""

    def __init__(self, page: Page, randomness_factor: float = 1.0):
        """
        Initialize simulator

        Args:
            page: Playwright Page instance
            randomness_factor: How random the behavior should be (0.0-2.0)
        """
        self.page = page
        self.randomness = randomness_factor

    def _bezier_curve(
        self,
        start: Tuple[float, float],
        end: Tuple[float, float],
        control_points: int = 2
    ) -> List[Tuple[float, float]]:
        """
        Generate smooth bezier curve for mouse movement

        Args:
            start: Starting (x, y) coordinates
            end: Ending (x, y) coordinates
            control_points: Number of control points (more = smoother)

        Returns:
            List of (x, y) coordinates along the curve
        """
        # Generate random control points
        controls = []
        for _ in range(control_points):
            x = random.uniform(
                min(start[0], end[0]),
                max(start[0], end[0])
            )
            y = random.uniform(
                min(start[1], end[1]),
                max(start[1], end[1])
            )
            controls.append((x, y))

        # Create curve points
        points = [start] + controls + [end]

        # Generate bezier curve
        steps = int(np.linalg.norm(np.array(end) - np.array(start)) / 10)
        steps = max(10, min(steps, 100))  # Between 10-100 steps

        curve_points = []
        for i in range(steps):
            t = i / (steps - 1)
            point = self._bezier_point(points, t)
            curve_points.append(point)

        return curve_points

    def _bezier_point(
        self,
        points: List[Tuple[float, float]],
        t: float
    ) -> Tuple[float, float]:
        """
        Calculate point on bezier curve at parameter t

        Args:
            points: Control points
            t: Parameter (0.0 to 1.0)

        Returns:
            (x, y) coordinate at parameter t
        """
        if len(points) == 1:
            return points[0]

        new_points = []
        for i in range(len(points) - 1):
            x = (1 - t) * points[i][0] + t * points[i + 1][0]
            y = (1 - t) * points[i][1] + t * points[i + 1][1]
            new_points.append((x, y))

        return self._bezier_point(new_points, t)

    async def move_mouse_to(
        self,
        x: float,
        y: float,
        duration: Optional[float] = None
    ) -> None:
        """
        Move mouse to coordinates using bezier curve

        Args:
            x: Target x coordinate
            y: Target y coordinate
            duration: Time in seconds (random if None)
        """
        # Get current mouse position (approximate)
        viewport = self.page.viewport_size
        current_x = random.randint(0, viewport['width'])
        current_y = random.randint(0, viewport['height'])

        # Generate smooth curve
        curve = self._bezier_curve((current_x, current_y), (x, y))

        # Calculate duration
        if duration is None:
            distance = math.sqrt((x - current_x)**2 + (y - current_y)**2)
            duration = (distance / 1000) * self.randomness

        # Move along curve
        step_duration = duration / len(curve)
        for point in curve:
            await self.page.mouse.move(point[0], point[1])
            await self.page.wait_for_timeout(int(step_duration * 1000))

    async def human_click(
        self,
        selector: Optional[str] = None,
        locator: Optional[Locator] = None,
        button: str = "left"
    ) -> None:
        """
        Perform human-like click with movement and hesitation

        Args:
            selector: CSS selector to click
            locator: Playwright Locator (alternative to selector)
            button: Mouse button ('left', 'right', 'middle')
        """
        # Get element to click
        if locator:
            element = locator
        elif selector:
            element = self.page.locator(selector).first
        else:
            raise ValueError("Either selector or locator must be provided")

        # Wait for element to be visible
        await element.wait_for(state="visible")

        # Get element bounding box
        box = await element.bounding_box()
        if not box:
            return

        # Random point within element (not always center)
        target_x = box['x'] + random.uniform(
            box['width'] * 0.3,
            box['width'] * 0.7
        )
        target_y = box['y'] + random.uniform(
            box['height'] * 0.3,
            box['height'] * 0.7
        )

        # Move to element with human-like curve
        await self.move_mouse_to(target_x, target_y)

        # Brief pause (hesitation)
        await self.page.wait_for_timeout(
            random.randint(50, 200)
        )

        # Hover for a moment
        await element.hover()
        await self.page.wait_for_timeout(
            random.randint(100, 300)
        )

        # Click
        await self.page.mouse.click(target_x, target_y, button=button)

        # Brief pause after click
        await self.page.wait_for_timeout(
            random.randint(50, 150)
        )

    async def human_scroll(
        self,
        direction: str = "down",
        distance: Optional[int] = None,
        smooth: bool = True
    ) -> None:
        """
        Perform human-like scrolling

        Args:
            direction: 'down', 'up', 'to_bottom', 'to_top'
            distance: Pixels to scroll (random if None)
            smooth: Use smooth scrolling
        """
        if distance is None:
            distance = random.randint(300, 800)

        if direction in ['to_bottom', 'to_top']:
            # Scroll to extremes gradually
            target = 0 if direction == 'to_top' else 999999
            await self.page.evaluate(f"""
                window.scrollTo({{
                    top: {target},
                    behavior: 'smooth'
                }});
            """)
            await self.page.wait_for_timeout(
                random.randint(1000, 2000)
            )
            return

        # Incremental scrolling
        scroll_delta = 100 if direction == "down" else -100
        steps = abs(distance // 100)

        for _ in range(steps):
            # Scroll a bit
            await self.page.mouse.wheel(0, scroll_delta)

            # Random pause between scrolls
            await self.page.wait_for_timeout(
                random.randint(50, 200)
            )

            # Occasionally pause longer (reading)
            if random.random() < 0.2:
                await self.page.wait_for_timeout(
                    random.randint(500, 1500)
                )

    async def simulate_reading(
        self,
        min_duration: float = 2.0,
        max_duration: float = 5.0
    ) -> None:
        """
        Simulate reading behavior with random scrolling and pauses

        Args:
            min_duration: Minimum reading time in seconds
            max_duration: Maximum reading time in seconds
        """
        duration = random.uniform(min_duration, max_duration)
        end_time = time.time() + duration

        while time.time() < end_time:
            # Small scroll down
            await self.page.mouse.wheel(0, random.randint(20, 80))

            # Pause (reading)
            await self.page.wait_for_timeout(
                random.randint(800, 2000)
            )

            # Sometimes scroll up (re-reading)
            if random.random() < 0.3:
                await self.page.mouse.wheel(0, random.randint(-50, -20))
                await self.page.wait_for_timeout(
                    random.randint(500, 1000)
                )

    async def random_mouse_movement(self) -> None:
        """
        Perform random mouse movements (idle behavior)
        """
        viewport = self.page.viewport_size

        # Move to random position
        target_x = random.randint(0, viewport['width'])
        target_y = random.randint(0, viewport['height'])

        await self.move_mouse_to(target_x, target_y)

    async def simulate_form_typing(
        self,
        selector: str,
        text: str,
        typing_speed: str = "human"
    ) -> None:
        """
        Type text with human-like delays and errors

        Args:
            selector: Input field selector
            text: Text to type
            typing_speed: 'slow', 'human', 'fast'
        """
        element = self.page.locator(selector).first
        await element.click()

        # Typing speeds (ms per character)
        speeds = {
            "slow": (100, 300),
            "human": (50, 150),
            "fast": (20, 80)
        }

        delay_range = speeds.get(typing_speed, speeds["human"])

        for i, char in enumerate(text):
            # Occasionally make a "typo" and correct it
            if random.random() < 0.05 and i > 0:  # 5% chance
                # Type wrong character
                wrong_char = random.choice('abcdefghijklmnopqrstuvwxyz')
                await element.type(wrong_char)
                await self.page.wait_for_timeout(
                    random.randint(100, 300)
                )
                # Backspace
                await element.press('Backspace')
                await self.page.wait_for_timeout(
                    random.randint(50, 150)
                )

            # Type correct character
            await element.type(char)

            # Random delay
            await self.page.wait_for_timeout(
                random.randint(*delay_range)
            )

            # Longer pause at punctuation
            if char in '.,;:!?':
                await self.page.wait_for_timeout(
                    random.randint(200, 500)
                )

    async def simulate_idle_time(
        self,
        min_seconds: float = 1.0,
        max_seconds: float = 3.0
    ) -> None:
        """
        Simulate idle/thinking time

        Args:
            min_seconds: Minimum idle time
            max_seconds: Maximum idle time
        """
        idle_time = random.uniform(min_seconds, max_seconds)
        await self.page.wait_for_timeout(int(idle_time * 1000))

        # Small random movement during idle
        if random.random() < 0.3:
            await self.random_mouse_movement()
