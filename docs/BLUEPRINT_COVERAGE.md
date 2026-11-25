# Blueprint coverage (v1.1) + In/Out pairs (v1.2)

Audit of every item in the *Kdenlive FX Pack: Expansion Blueprint* against the v1.0 pack, done before
building anything, so nothing is implemented twice. **Present** = an existing preset already does essentially
the same thing (nothing added). **Partial** = the effect existed but a variant was missing (direction, In/Out
half, intensity tier) – only that variant was added. **New** = not in v1.0, implemented in v1.1.

Totals: **41 blueprint items** – 12 already present, 8 partial (missing variants added), 21 new. New files: 63 presets + 16 sound effects.

| Category | Items | Present | Partial | New | New preset files |
|---|---|---|---|---|---|
| 1. Object & Graphic Movements | 11 | 5 | 2 | 4 | 19 |
| 2. Camera Motion & Framing | 8 | 2 | 4 | 2 | 12 |
| 3. Focus, Callout & Explainer Utilities | 6 | 0 | 2 | 4 | 19 |
| 4. Stylistic Visuals & Impact Accents | 7 | 4 | 0 | 3 | 3 |
| 5. Text & Kinetic Title Presets | 5 | 1 | 0 | 4 | 5 |
| 6. Audio FX Presets | 4 | 0 | 0 | 4 | 5 |
| + Sound effects (requested with the audio presets) | – | – | – | – | 16 WAV files |

## 1. Object & Graphic Movements

| # | Blueprint item | Status | Existing v1.0 preset(s) | New in v1.1 | Notes |
|---|---|---|---|---|---|
| 1.1 | Smooth Slide-In / Slide-Out (4 directions) | ✅ present | `ouzfx_anim_slide_in_left`<br>`ouzfx_anim_slide_in_right`<br>`ouzfx_anim_slide_in_top`<br>`ouzfx_anim_slide_in_bottom`<br>`ouzfx_comp_slide_out_left`<br>`ouzfx_comp_slide_out_right`<br>`ouzfx_comp_slide_out_up`<br>`ouzfx_comp_slide_out_down` | – (no duplicate built) | In = effect templates with expo ease-out; Out = compositions with expo ease-in (already split In/Out). |
| 1.2 | Overshoot / Bounce Slide | 🆕 new | – | `ouzfx_afx_move_overshoot_slide_in_left`<br>`ouzfx_afx_move_overshoot_slide_in_right`<br>`ouzfx_afx_move_overshoot_slide_in_top`<br>`ouzfx_afx_move_overshoot_slide_in_bottom` | 4 directions, back ease-out. |
| 1.3 | Whip-Slide (with simulated motion blur) | ✅ present | `ouzfx_anim_slide_in_left`<br>`ouzfx_anim_whip_in`<br>`ouzfx_fast_motion_slide_l` | – (no duplicate built) | The v1.0 slides already carry a directional-blur peak; Whip-In is the 6-frame fast tier. Missing push directions are added under 2.5. |
| 1.4 | Masked Edge Reveal | 🆕 new | – | `ouzfx_afx_move_masked_edge_reveal_up`<br>`ouzfx_afx_move_masked_edge_reveal_down`<br>`ouzfx_afx_move_masked_edge_reveal_left`<br>`ouzfx_afx_move_masked_edge_reveal_right` | Transform slide + static crop mask, emerges from the centre line (4 directions). |
| 1.5 | Elastic Pop-In / Pop-Out | ✅ present | `ouzfx_anim_pop_in`<br>`ouzfx_anim_elastic_in`<br>`ouzfx_comp_pop_in`<br>`ouzfx_comp_pop_out`<br>`ouzfx_text_pop` | – (no duplicate built) | Back-overshoot pop-in and anticipation pop-out already exist (Kdenlive/MLT back easing, so the overshoot is stronger than 108%). |
| 1.6 | Drop & Gravity Bounce | ✅ present | `ouzfx_anim_bounce_in` | – (no duplicate built) | Drops from the top edge with bounce easing (decaying rebounds). |
| 1.7 | Idle Float / Gentle Hover | 🆕 new | – | `ouzfx_afx_move_idle_float_gentle`<br>`ouzfx_afx_move_idle_float_strong` | Closest v1.0 presets (Text Wiggle = fast ±3° wiggle, Walking Bounce = camera bob) are different motions. |
| 1.8 | Perspective Card Tilt / 3D Swing-In | ➕ partial | `ouzfx_screen_tilt_left`<br>`ouzfx_screen_tilt_right`<br>`ouzfx_screen_tilt_back`<br>`ouzfx_screen_tilt_to_flat` | `ouzfx_afx_move_card_3d_swing_in_left`<br>`ouzfx_afx_move_card_3d_swing_in_right` | Static tilts and an in-place swing existed; added the missing swing-IN from off-screen (left/right). |
| 1.9 | Hinge / Pendulum Swing-In | 🆕 new | – | `ouzfx_afx_move_hinge_swing_in_top_left`<br>`ouzfx_afx_move_hinge_swing_in_top_right`<br>`ouzfx_afx_move_pendulum_swing_settle` | Top-left hinge, top-right hinge, top-centre pendulum. |
| 1.10 | Corner PiP Snap (4 corners) | ➕ partial | `ouzfx_comp_picture_in_picture` | `ouzfx_afx_move_pip_snap_top_left`<br>`ouzfx_afx_move_pip_snap_top_right`<br>`ouzfx_afx_move_pip_snap_bottom_left`<br>`ouzfx_afx_move_pip_snap_bottom_right` | v1.0 had one bottom-right pop-in composition; added full-screen→corner snaps for all 4 corners (rounded edges, shadow via 5.5). |
| 1.11 | Spin-In / Vortex Exit | ✅ present | `ouzfx_anim_spin_in`<br>`ouzfx_comp_spin_in`<br>`ouzfx_comp_spin_out` | – (no duplicate built) |  |

## 2. Camera Motion & Framing

| # | Blueprint item | Status | Existing v1.0 preset(s) | New in v1.1 | Notes |
|---|---|---|---|---|---|
| 2.1 | Zoom Punch (In / Out) | ✅ present | `ouzfx_zoom_punch_in`<br>`ouzfx_zoom_punch_in_out`<br>`ouzfx_fast_smash_cut`<br>`ouzfx_zoom_boom` | – (no duplicate built) |  |
| 2.2 | Smooth Ken Burns Drift (in / out / pan) | ➕ partial | `ouzfx_zoom_ken_burns_in`<br>`ouzfx_zoom_ken_burns_out`<br>`ouzfx_comp_ken_burns_in`<br>`ouzfx_comp_ken_burns_out`<br>`ouzfx_comp_ken_burns_pan` | `ouzfx_afx_cam_ken_burns_pan_right_to_left`<br>`ouzfx_afx_cam_ken_burns_pan_up`<br>`ouzfx_afx_cam_ken_burns_pan_down` | Zoom in/out and pan L→R existed; added the missing pan directions (R→L, up, down). |
| 2.3 | Handheld Camera Sway | ✅ present | `ouzfx_shake_handheld_light`<br>`ouzfx_shake_micro_jitter` | – (no duplicate built) |  |
| 2.4 | Impact Shake / Screen Quake (Light, Medium, Heavy) | ➕ partial | `ouzfx_shake_heavy_impact`<br>`ouzfx_shake_earthquake` | `ouzfx_afx_cam_impact_shake_light`<br>`ouzfx_afx_cam_impact_shake_medium` | Heavy tier existed; added the Light and Medium tiers. |
| 2.5 | Whip Pan Push (4 directions) | ➕ partial | `ouzfx_fast_motion_slide_l`<br>`ouzfx_comp_whip_left` | `ouzfx_afx_cam_whip_pan_push_right`<br>`ouzfx_afx_cam_whip_pan_push_up`<br>`ouzfx_afx_cam_whip_pan_push_down` | Push-left (effect) and whip compositions existed; added push right / up / down. |
| 2.6 | Heartbeat Pulse | 🆕 new | – | `ouzfx_afx_cam_heartbeat_pulse` | Beat Pulse ×4 is uniform single pulses; heartbeat = slow double 'lub-dub' + darkening throb. |
| 2.7 | Dutch Angle Tilt | 🆕 new | – | `ouzfx_afx_cam_dutch_angle_subtle_8deg`<br>`ouzfx_afx_cam_dutch_angle_strong_15deg` | 8° and 15° tiers with automatic cover-zoom. |
| 2.8 | Cinematic Letterbox Reveal | ➕ partial | `ouzfx_look_bars_slide_in`<br>`ouzfx_look_cinematic_239` | `ouzfx_afx_cam_cinematic_bars_slide_out` | Bars slide-in existed; added the matching slide-out (In/Out split). |

## 3. Focus, Callout & Explainer Utilities

| # | Blueprint item | Status | Existing v1.0 preset(s) | New in v1.1 | Notes |
|---|---|---|---|---|---|
| 3.1 | Background Dim & Blur | 🆕 new | – | `ouzfx_afx_util_bg_dim_blur_in`<br>`ouzfx_afx_util_bg_dim_blur_out` | In and Out. |
| 3.2 | Spotlight Vignette Focus (animated) | ➕ partial | `ouzfx_look_soft_vignette` | `ouzfx_afx_util_spotlight_focus_in`<br>`ouzfx_afx_util_spotlight_focus_out` | Only a static vignette existed; added animated spotlight In / Out. |
| 3.3 | Highlighter Wipe | 🆕 new | – | `ouzfx_afx_util_highlighter_wipe` | For a Color clip: 45% marker band with left-to-right crop wipe. |
| 3.4 | Split-Screen Presets (L/R, T/B, optional slide) | 🆕 new | – | `ouzfx_afx_util_split_screen_left`<br>`ouzfx_afx_util_split_screen_left_slide_in`<br>`ouzfx_afx_util_split_screen_right`<br>`ouzfx_afx_util_split_screen_right_slide_in`<br>`ouzfx_afx_util_split_screen_top`<br>`ouzfx_afx_util_split_screen_top_slide_in`<br>`ouzfx_afx_util_split_screen_bottom`<br>`ouzfx_afx_util_split_screen_bottom_slide_in` | 4 static halves + 4 slide-in versions. |
| 3.5 | Censor / Redact Blur Box | 🆕 new | – | `ouzfx_afx_util_censor_pixelate_box`<br>`ouzfx_afx_util_censor_blur_box` | Pixelate and heavy-blur versions (Alpha shapes mask). |
| 3.6 | Magnifying Zoom Callout (quadrants, back to 100%) | ➕ partial | `ouzfx_zoom_screen_tl`<br>`ouzfx_zoom_screen_tr`<br>`ouzfx_zoom_screen_bl`<br>`ouzfx_zoom_screen_br`<br>`ouzfx_zoom_screen_c`<br>`ouzfx_zoom_screen_out` | `ouzfx_afx_cam_zoom_callout_return_top_left`<br>`ouzfx_afx_cam_zoom_callout_return_top_right`<br>`ouzfx_afx_cam_zoom_callout_return_bottom_left`<br>`ouzfx_afx_cam_zoom_callout_return_bottom_right` | Zoom-in to each quadrant existed, but the return only worked from the centre; added a return for each corner. |

## 4. Stylistic Visuals & Impact Accents

| # | Blueprint item | Status | Existing v1.0 preset(s) | New in v1.1 | Notes |
|---|---|---|---|---|---|
| 4.1 | RGB Split / Chromatic Aberration Burst | ✅ present | `ouzfx_glitch_rgb_split_hit`<br>`ouzfx_glitch_digital_burst` | – (no duplicate built) |  |
| 4.2 | Flash Cut / Exposure Spike (white & warm) | ✅ present | `ouzfx_flash_white`<br>`ouzfx_flash_black`<br>`ouzfx_style_film_burn` | – (no duplicate built) | White flash and warm over-exposure flash already exist. |
| 4.3 | Dramatic Desaturate ('Record Scratch' Freeze) | 🆕 new | – | `ouzfx_afx_style_record_scratch_freeze` | B&W Flashback is a static film look; this adds high-contrast B&W + slow push. |
| 4.4 | VHS / Retro CRT Stack | ✅ present | `ouzfx_style_vhs` | – (no duplicate built) |  |
| 4.5 | Dreamy Bloom / Halation Glow | ✅ present | `ouzfx_style_light_leak` | – (no duplicate built) | Glow + lifted, warm highlights (halation look). |
| 4.6 | Glitch Flicker | 🆕 new | – | `ouzfx_afx_style_glitch_flicker` | Opacity drops + horizontal displacement + light block distortion. |
| 4.7 | Red Alert / Damage Pulse | 🆕 new | – | `ouzfx_afx_style_damage_pulse_red` | Red Moment tints the whole frame; this pulses only the edges. |

## 5. Text & Kinetic Title Presets

| # | Blueprint item | Status | Existing v1.0 preset(s) | New in v1.1 | Notes |
|---|---|---|---|---|---|
| 5.1 | Short-Form Word Pop (85→105→100%) | 🆕 new | – | `ouzfx_afx_move_text_word_pop_shorts` | New speed tier: Text Pop is an 8-frame 30→100% pop. |
| 5.2 | Rise & Fade Lower Third | ✅ present | `ouzfx_text_rise` | – (no duplicate built) | Rises 6% of the frame height (≈ 65 px at 1080p) with fade. |
| 5.3 | Typewriter Line Wipe | 🆕 new | – | `ouzfx_afx_move_text_typewriter_wipe_fast`<br>`ouzfx_afx_move_text_typewriter_wipe_slow` | Fast (1 s) and Slow (2 s). Note: v1.0 slug text_typewriter_flash is the 'Highlight Flash', not a wipe. |
| 5.4 | Glitch-In Title | 🆕 new | – | `ouzfx_afx_move_text_glitch_in` |  |
| 5.5 | Drop Shadow Polish | 🆕 new | – | `ouzfx_afx_util_drop_shadow_polish` | Static two-layer shadow, Kdenlive 25.04+. |

## 6. Audio FX Presets

| # | Blueprint item | Status | Existing v1.0 preset(s) | New in v1.1 | Notes |
|---|---|---|---|---|---|
| 6.1 | Underwater / Muffled Room | 🆕 new | – | `ouzfx_afx_audio_underwater_muffled` |  |
| 6.2 | Walkie-Talkie / Telephone Voice | 🆕 new | – | `ouzfx_afx_audio_telephone_voice`<br>`ouzfx_afx_audio_walkie_talkie_radio` | Two variants: clean telephone and crunchy radio. |
| 6.3 | Dramatic Echo / Hall Reverb | 🆕 new | – | `ouzfx_afx_audio_hall_echo_reverb` | Kdenlive hides FFmpeg aecho/acompressor, so built from included delay + limiter effects. |
| 6.4 | Voiceover Quick Polish | 🆕 new | – | `ouzfx_afx_audio_voiceover_quick_polish` | High-pass + Dynamic Loudness leveler + limiter. |

## In/Out pairs (v1.2)

Every entrance / intro animation in the pack was checked for a matching exit. Intros that already had one were left alone; the rest got an Out preset in v1.2 (time-mirrored timing, ease-in acceleration).

**How the Out timing works in Kdenlive** – compositions use `0=`/`-1=` keyframes, so an Out *composition* always ends exactly at the end of the composition, whatever its length. Kdenlive re-bases *effect template* keyframes on the clip start and drops end-relative (negative) keyframes when a template is applied, so Out *templates* work like the whip pushes: razor N frames before the end and drop the template on that last piece – the layer is gone on its last frame. Every Out preset is melt-tested that way (`tools/out_tests.py`): its first frame matches the last frame of its intro and its last frame shows only the background (PiP and Dutch Angle Outs: the clip back at rest; Screen_Swing_Back_Out: the tilted panel).

### New in v1.2

| Intro | New Out preset(s) | Type |
|---|---|---|
| OuzFX Anim · Slide In from Left<br><sub>`ouzfx_anim_slide_in_left`</sub> | **OuzFX AFX_Move_Whip_Slide_Out_Left** | effect template |
| OuzFX Anim · Slide In from Right<br><sub>`ouzfx_anim_slide_in_right`</sub> | **OuzFX AFX_Move_Whip_Slide_Out_Right** | effect template |
| OuzFX Anim · Slide In from Top<br><sub>`ouzfx_anim_slide_in_top`</sub> | **OuzFX AFX_Move_Whip_Slide_Out_Up** | effect template |
| OuzFX Anim · Slide In from Bottom<br><sub>`ouzfx_anim_slide_in_bottom`</sub> | **OuzFX AFX_Move_Whip_Slide_Out_Down** | effect template |
| OuzFX AFX_Move_Overshoot_Slide_In_Left<br><sub>`ouzfx_afx_move_overshoot_slide_in_left`</sub> | **OuzFX AFX_Move_Overshoot_Slide_Out_Left**<br>**OuzFX AFX_Move_Overshoot_Slide_Out_Left_AnyLength** | composition, effect template |
| OuzFX AFX_Move_Overshoot_Slide_In_Right<br><sub>`ouzfx_afx_move_overshoot_slide_in_right`</sub> | **OuzFX AFX_Move_Overshoot_Slide_Out_Right**<br>**OuzFX AFX_Move_Overshoot_Slide_Out_Right_AnyLength** | composition, effect template |
| OuzFX AFX_Move_Overshoot_Slide_In_Top<br><sub>`ouzfx_afx_move_overshoot_slide_in_top`</sub> | **OuzFX AFX_Move_Overshoot_Slide_Out_Top**<br>**OuzFX AFX_Move_Overshoot_Slide_Out_Top_AnyLength** | composition, effect template |
| OuzFX AFX_Move_Overshoot_Slide_In_Bottom<br><sub>`ouzfx_afx_move_overshoot_slide_in_bottom`</sub> | **OuzFX AFX_Move_Overshoot_Slide_Out_Bottom**<br>**OuzFX AFX_Move_Overshoot_Slide_Out_Bottom_AnyLength** | composition, effect template |
| OuzFX AFX_Move_Masked_Edge_Reveal_Up<br><sub>`ouzfx_afx_move_masked_edge_reveal_up`</sub> | **OuzFX AFX_Move_Masked_Edge_Reveal_Up_Out** | effect template |
| OuzFX AFX_Move_Masked_Edge_Reveal_Down<br><sub>`ouzfx_afx_move_masked_edge_reveal_down`</sub> | **OuzFX AFX_Move_Masked_Edge_Reveal_Down_Out** | effect template |
| OuzFX AFX_Move_Masked_Edge_Reveal_Left<br><sub>`ouzfx_afx_move_masked_edge_reveal_left`</sub> | **OuzFX AFX_Move_Masked_Edge_Reveal_Left_Out** | effect template |
| OuzFX AFX_Move_Masked_Edge_Reveal_Right<br><sub>`ouzfx_afx_move_masked_edge_reveal_right`</sub> | **OuzFX AFX_Move_Masked_Edge_Reveal_Right_Out** | effect template |
| OuzFX Anim · Bounce In (Drop)<br><sub>`ouzfx_anim_bounce_in`</sub> | **OuzFX AFX_Move_Bounce_Drop_Out**<br>**OuzFX AFX_Move_Bounce_Drop_Out_AnyLength** | composition, effect template |
| OuzFX Anim · Elastic Zoom-In<br><sub>`ouzfx_anim_elastic_in`</sub> | **OuzFX AFX_Move_Elastic_Zoom_Out**<br>**OuzFX AFX_Move_Elastic_Zoom_Out_AnyLength** | composition, effect template |
| OuzFX Anim · Blur-In<br><sub>`ouzfx_anim_blur_in`</sub> | **OuzFX AFX_Move_Blur_Out** | effect template |
| OuzFX Screen 3D · Swing to Front<br><sub>`ouzfx_screen_tilt_to_flat`</sub> | **OuzFX AFX_Move_Screen_Swing_Back_Out** | effect template |
| OuzFX Screen 3D · Floating Screen · Pop In<br><sub>`ouzfx_screen_pop_in`</sub> | **OuzFX AFX_Move_Screen_Pop_Out** | effect template |
| OuzFX AFX_Move_Card_3D_Swing_In_Left<br><sub>`ouzfx_afx_move_card_3d_swing_in_left`</sub> | **OuzFX AFX_Move_Card_3D_Swing_Out_Left** | effect template |
| OuzFX AFX_Move_Card_3D_Swing_In_Right<br><sub>`ouzfx_afx_move_card_3d_swing_in_right`</sub> | **OuzFX AFX_Move_Card_3D_Swing_Out_Right** | effect template |
| OuzFX AFX_Move_Hinge_Swing_In_Top_Left<br><sub>`ouzfx_afx_move_hinge_swing_in_top_left`</sub> | **OuzFX AFX_Move_Hinge_Swing_Out_Top_Left** | effect template |
| OuzFX AFX_Move_Hinge_Swing_In_Top_Right<br><sub>`ouzfx_afx_move_hinge_swing_in_top_right`</sub> | **OuzFX AFX_Move_Hinge_Swing_Out_Top_Right** | effect template |
| OuzFX AFX_Move_PiP_Snap_Top_Left<br><sub>`ouzfx_afx_move_pip_snap_top_left`</sub> | **OuzFX AFX_Move_PiP_Snap_Top_Left_Out** | effect template |
| OuzFX AFX_Move_PiP_Snap_Top_Right<br><sub>`ouzfx_afx_move_pip_snap_top_right`</sub> | **OuzFX AFX_Move_PiP_Snap_Top_Right_Out** | effect template |
| OuzFX AFX_Move_PiP_Snap_Bottom_Left<br><sub>`ouzfx_afx_move_pip_snap_bottom_left`</sub> | **OuzFX AFX_Move_PiP_Snap_Bottom_Left_Out** | effect template |
| OuzFX AFX_Move_PiP_Snap_Bottom_Right<br><sub>`ouzfx_afx_move_pip_snap_bottom_right`</sub> | **OuzFX AFX_Move_PiP_Snap_Bottom_Right_Out** | effect template |
| OuzFX AFX_Move_Text_Word_Pop_Shorts<br><sub>`ouzfx_afx_move_text_word_pop_shorts`</sub> | **OuzFX AFX_Move_Text_Word_Pop_Shorts_Out** | effect template |
| OuzFX Text · Text Rise<br><sub>`ouzfx_text_rise`</sub> | **OuzFX AFX_Move_Text_Rise_Fade_Out**<br>**OuzFX AFX_Move_Text_Rise_Fade_Out_AnyLength** | composition, effect template |
| OuzFX AFX_Move_Text_Typewriter_Wipe_Fast<br><sub>`ouzfx_afx_move_text_typewriter_wipe_fast`</sub> | **OuzFX AFX_Move_Text_Typewriter_Wipe_Fast_Out** | effect template |
| OuzFX AFX_Move_Text_Typewriter_Wipe_Slow<br><sub>`ouzfx_afx_move_text_typewriter_wipe_slow`</sub> | **OuzFX AFX_Move_Text_Typewriter_Wipe_Slow_Out** | effect template |
| OuzFX AFX_Move_Text_Glitch_In<br><sub>`ouzfx_afx_move_text_glitch_in`</sub> | **OuzFX AFX_Move_Text_Glitch_Out** | effect template |
| OuzFX AFX_Util_Split_Screen_Left_Slide_In<br><sub>`ouzfx_afx_util_split_screen_left_slide_in`</sub> | **OuzFX AFX_Util_Split_Screen_Left_Slide_Out** | effect template |
| OuzFX AFX_Util_Split_Screen_Right_Slide_In<br><sub>`ouzfx_afx_util_split_screen_right_slide_in`</sub> | **OuzFX AFX_Util_Split_Screen_Right_Slide_Out** | effect template |
| OuzFX AFX_Util_Split_Screen_Top_Slide_In<br><sub>`ouzfx_afx_util_split_screen_top_slide_in`</sub> | **OuzFX AFX_Util_Split_Screen_Top_Slide_Out** | effect template |
| OuzFX AFX_Util_Split_Screen_Bottom_Slide_In<br><sub>`ouzfx_afx_util_split_screen_bottom_slide_in`</sub> | **OuzFX AFX_Util_Split_Screen_Bottom_Slide_Out** | effect template |
| OuzFX AFX_Util_Highlighter_Wipe<br><sub>`ouzfx_afx_util_highlighter_wipe`</sub> | **OuzFX AFX_Util_Highlighter_Wipe_Out** | effect template |
| OuzFX AFX_Cam_Dutch_Angle_Subtle_8deg<br><sub>`ouzfx_afx_cam_dutch_angle_subtle_8deg`</sub> | **OuzFX AFX_Cam_Dutch_Angle_Subtle_8deg_Out** | effect template |
| OuzFX AFX_Cam_Dutch_Angle_Strong_15deg<br><sub>`ouzfx_afx_cam_dutch_angle_strong_15deg`</sub> | **OuzFX AFX_Cam_Dutch_Angle_Strong_15deg_Out** | effect template |
| OuzFX Trans · Whip Pan Left<br><sub>`ouzfx_comp_whip_left`</sub> | **OuzFX AFX_Cam_Whip_Push_Out_Left** | composition |
| OuzFX Trans · Whip Pan Right<br><sub>`ouzfx_comp_whip_right`</sub> | **OuzFX AFX_Cam_Whip_Push_Out_Right** | composition |
| OuzFX Trans · Whip Pan Up<br><sub>`ouzfx_comp_whip_up`</sub> | **OuzFX AFX_Cam_Whip_Push_Out_Up** | composition |
| OuzFX Trans · Whip Pan Down<br><sub>`ouzfx_comp_whip_down`</sub> | **OuzFX AFX_Cam_Whip_Push_Out_Down** | composition |
| OuzFX Screen 3D · Picture-in-Picture Corner (Pop)<br><sub>`ouzfx_comp_picture_in_picture`</sub> | **OuzFX AFX_Move_PiP_Corner_Pop_Out** | composition |

### Already had an Out before v1.2 (not rebuilt)

| Intro(s) | Existing Out(s) | Note |
|---|---|---|
| OuzFX Anim · Slide In from Left<br>OuzFX Anim · Slide In from Right<br>OuzFX Anim · Slide In from Top<br>OuzFX Anim · Slide In from Bottom | OuzFX Anim · Slide Out Left<br>OuzFX Anim · Slide Out Right<br>OuzFX Anim · Slide Out Up<br>OuzFX Anim · Slide Out Down | Out compositions (expo ease-in). v1.2 adds the effect-template whip-slide Outs with motion blur (below). |
| OuzFX Anim · Whip-In | OuzFX Fast · Motion-Blur Push Left<br>OuzFX AFX_Cam_Whip_Pan_Push_Right<br>OuzFX AFX_Cam_Whip_Pan_Push_Up<br>OuzFX AFX_Cam_Whip_Pan_Push_Down | 6–8 frame whip-outs with heavy blur (fast tier). Motion-Blur Push Left is the exact mirror of Whip-In. |
| OuzFX Trans · Whip Pan Left<br>OuzFX Trans · Whip Pan Right<br>OuzFX Trans · Whip Pan Up<br>OuzFX Trans · Whip Pan Down | OuzFX Anim · Slide Out Left<br>OuzFX Anim · Slide Out Right<br>OuzFX Anim · Slide Out Up<br>OuzFX Anim · Slide Out Down | Slide Out = time-reverse of Whip Pan (expo in vs. expo out). v1.2 adds the two-clip Whip_Push_Out transitions. |
| OuzFX Anim · Pop-In<br>OuzFX Anim · Pop In (Any Length)<br>OuzFX Text · Text Pop | OuzFX Anim · Pop Out |  |
| OuzFX Anim · Spin-In<br>OuzFX Trans · Spin In | OuzFX Trans · Spin Out |  |
| OuzFX Anim · Fade + Scale In | OuzFX Anim · Fade + Scale Out |  |
| OuzFX Trans · Zoom-Through In<br>OuzFX Text · Text Slam | OuzFX Trans · Zoom-Through Out | Slam reversed = rush towards the camera and fade. |
| OuzFX Fast · Smash Cut In | OuzFX Fast · Rush Zoom | Rush Zoom is the accelerating exit of a smash cut. |
| OuzFX Look · Cinematic Bars Slide-In | OuzFX AFX_Cam_Cinematic_Bars_Slide_Out |  |
| OuzFX Screen Zoom · Zoom to Top-Left (Screen Rec)<br>OuzFX Screen Zoom · Zoom to Top-Right (Screen Rec)<br>OuzFX Screen Zoom · Zoom to Bottom-Left (Screen Rec)<br>OuzFX Screen Zoom · Zoom to Bottom-Right (Screen Rec)<br>OuzFX Screen Zoom · Zoom to Center (Screen Rec) | OuzFX AFX_Cam_Zoom_Callout_Return_Top_Left<br>OuzFX AFX_Cam_Zoom_Callout_Return_Top_Right<br>OuzFX AFX_Cam_Zoom_Callout_Return_Bottom_Left<br>OuzFX AFX_Cam_Zoom_Callout_Return_Bottom_Right<br>OuzFX Screen Zoom · Zoom Back Out (Screen Rec) |  |
| OuzFX Zoom · Slow Push-In (5 s)<br>OuzFX Zoom · Ken Burns Push-In (Any Length) | OuzFX Zoom · Slow Pull-Out (5 s)<br>OuzFX Zoom · Ken Burns Pull-Out (Any Length) |  |
| OuzFX AFX_Util_BG_Dim_Blur_In | OuzFX AFX_Util_BG_Dim_Blur_Out |  |
| OuzFX AFX_Util_Spotlight_Focus_In | OuzFX AFX_Util_Spotlight_Focus_Out |  |

### No Out needed

| Kind | Presets |
|---|---|
| Loops / continuous | shake_*, Idle_Float_*, Text Wiggle, Walking Bounce, Beat Pulse, Heartbeat_Pulse – they have no entry to reverse. |
| Hits that return to rest | Punch In-Out, Boom Zoom, Zoom Bounce, Impact hits/shakes, RGB Split Hit, Glitch Burst/Flicker, flashes, Film Burn, Red Moment, Damage Pulse, Highlight Flash, Pendulum_Swing_Settle (starts in frame and settles). |
| Static looks / holds | VHS, film looks, vignette, Cinematic 2.39, Zoom Cut, Punch-In 115% (a hold – reverse it with Zoom Back Out / Punch In-Out), Split_Screen_* (static halves), censor boxes, drop shadow, Perspective Screen tilts. |
| Record_Scratch_Freeze | a style hold, not an entrance. |

## Sound effects (new)

| File | Length | Description |
|---|---|---|
| `sfx/risers/ouzfx_riser_short_2s.wav` | 2.00 s | Short riser (2 s): filtered noise + detuned saw sweep that builds into a cut. |
| `sfx/risers/ouzfx_riser_long_4s.wav` | 4.00 s | Long build-up riser (4 s) with accelerating tremolo – intros, reveals. |
| `sfx/risers/ouzfx_riser_reverse_cymbal_2s.wav` | 2.00 s | Reverse-cymbal swell (2 s) that sucks into the cut. |
| `sfx/risers/ouzfx_riser_tension_3s.wav` | 3.00 s | Tension riser (3 s): rising detuned synth with speeding tremolo. |
| `sfx/risers/ouzfx_downlifter_2s.wav` | 2.00 s | Downlifter (2 s): the riser in reverse – falls away after a drop. |
| `sfx/pops/ouzfx_pop_soft.wav` | 0.09 s | Soft pop (90 ms) – captions, stickers, gentle UI pops. |
| `sfx/pops/ouzfx_pop_hard.wav` | 0.08 s | Hard pop (80 ms) with a click transient – punchy text slams. |
| `sfx/pops/ouzfx_pop_bubble.wav` | 0.12 s | Bubble 'bloop' (120 ms) with an upward pitch – emojis, notifications. |
| `sfx/pops/ouzfx_pop_click_ui.wav` | 0.03 s | Tiny UI click (30 ms) – cursor clicks, checkmarks, counters. |
| `sfx/whooshes/ouzfx_whoosh_fast.wav` | 0.40 s | Fast whoosh (0.4 s, panned L→R) – slides and quick transitions. |
| `sfx/whooshes/ouzfx_whoosh_slow.wav` | 1.20 s | Slow airy whoosh (1.2 s) – Ken Burns, fades, soft reveals. |
| `sfx/whooshes/ouzfx_whoosh_heavy.wav` | 0.80 s | Heavy whoosh (0.8 s) with a sub sweep – zoom-throughs, big moves. |
| `sfx/whooshes/ouzfx_swoosh_whip.wav` | 0.25 s | Whip swoosh (0.25 s), bright and snappy – whip pans, Whip-In. |
| `sfx/whooshes/ouzfx_whoosh_reverse_suck.wav` | 0.60 s | Reverse 'suck' whoosh (0.6 s) that ends on the cut. |
| `sfx/impacts/ouzfx_impact_boom.wav` | 1.60 s | Cinematic boom (1.6 s): sub kick + crack + rumble – Boom Zoom, Impact Hit. |
| `sfx/impacts/ouzfx_impact_punch.wav` | 0.50 s | Short punchy hit (0.5 s) – shakes, smash cuts, text slams. |

## Design tips from the blueprint (section 7)

* **Normalized geometry** – every preset is authored in fractions of the frame and generated per resolution (1080p, 4K, vertical 9:16) because Kdenlive's Transform widget only round-trips pixel rectangles; `install.sh --profile` picks the set. Mask/spot presets use resolution-independent 0–1 coordinates.
* **Split In / Out** – new presets come as In/Out pairs where it matters (Dim & Blur, Spotlight, Bars, Zoom Callout returns).
* **Speed / intensity tiers** – Impact Shake Light/Medium (+ v1.0 Heavy), Idle Float Gentle/Strong, Dutch Angle 8°/15°, Typewriter Fast/Slow.
* **Naming** – new presets use `OuzFX AFX_Move_` / `AFX_Cam_` / `AFX_Style_` / `AFX_Util_` / `AFX_Audio_`. v1.0 names were kept unchanged so existing projects keep working.
