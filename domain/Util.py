

class Util:
	
	def __init__(self):
		pass
	
	@staticmethod
	def seconds_to_time_string(seconds: float):
		
		if isinstance(seconds, float):
			pass
		elif isinstance(seconds, int):
			seconds = float(seconds)
		else:
			raise AssertionError("Seconds must be an int or float")
		
		# Map
		dt_map = {
			"year": 31536000.0,
			"month": 2592000.0,
			"week": 604800.0,
			"day": 86400.0,
			"hour": 3600.0,
			"minute": 60.0,
			"second": 1.0
		}
		
		s_parts = []
		for unit_label in dt_map.keys():
			unit_seconds = dt_map[unit_label]
			if seconds >= unit_seconds:
				unit_count = int(seconds / unit_seconds)
				s_parts.append("{} {}{}".format(
					unit_count, unit_label,
					"" if unit_count == 1 else "s"
				))
				seconds -= unit_seconds * unit_count
		
		s = ", ".join(s_parts)
		
		return s
