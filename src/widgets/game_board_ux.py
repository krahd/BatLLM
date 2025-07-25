def _on_keyboard_down(self, keyboard, keycode, text, modifiers):
		"""Handles keyboard input for bot commands."""	

		if modifiers and 'shift' in modifiers:
			bot_id = 2
		else:
			bot_id = 1

		bot = self.get_bot_by_id(bot_id)


		if keycode[1] == 'escape':            
				keyboard.release()

		else:
			match keycode[1]:
				
				case 'm':
					bot.move()
				  
				case 'r':
					bot.rotate(.2)

				case 't':
					bot.rotate(-.2)
				  
				case 's':
					bot.toggle_shield()

				case 'spacebar':           
					# TODO move bot sounds inside the bot class
					if not bot.shield:
						Clock.schedule_once(lambda dt: self.play_sound(self.snd_shoot))

					bullet = bot.shoot()                    
						

					self.bullet_alpha = 1

					alive = True                    
					damaged_bot_id = None

					if bullet is None:
						alive = False

					while alive:

						(alive, damaged_bot_id) = bullet.update(self.bots)

						# only draw bulltes outside the shooting bot                        
						dist = ((bullet.x - bot.x) ** 2 + (bullet.y - bot.y) ** 2) ** 0.5
						if dist *.97 > bot.diameter / 2:
							self.bulletTrace.append((bullet.x, bullet.y))
					
					if damaged_bot_id is not None:
						print(f"Bot {damaged_bot_id} was hit by a bullet from Bot {bot.id}!")


						Clock.schedule_once(lambda dt: self.play_sound(self.snd_hit))

						self.get_bot_by_id(damaged_bot_id)
						self.get_bot_by_id(damaged_bot_id).damage()
						
					else:
						print(f"Bullet from Bot {bot.id} did not hit any bot.")
												   
			
			return True