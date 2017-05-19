from wishbonedevice import WishBoneDevice
import fractions as _frac
import math

class LMX2581(WishBoneDevice):
	""" LMX2581 Frequency Synthesizer """

	DICTS = [
	#00
		{
		'ID' : 1 << 31,
		'FRAC_DITHER' : 0b11 << 29,
		'NO_FCAL' : 1 << 28,
		'PLL_N' : 0b111111111111 << 16, # PLL[11:0] PLL Feedback Divider Value
		'PLL_NUM_L' : 0b111111111111 << 4, # PLL_NUM[11:0] PLL Fractional Numerator
		},
	#01
		{
		'CPG' : 0b11111 << 27,
		'VCO_SEL' : 0b11 << 25,
		'PLL_NUM_H' : 0b1111111111 << 15, # PLL_NUM[21:12] PLL Fractional Numerator
		'FRAC_ORDER' : 0b111 << 12,
		'PLL_R' : 0b11111111 << 4, # PLL_R[7:0] divides the OSCin frequency
		},
	#02
		{
		'OSC_2X' : 1 << 29,
		'CPP' : 1 << 27,
		'PLL_DEN' : 0b1111111111111111111111 << 4, # PLL_DEN[21:0] PLL Fractional Denominator
		},
	#03
		{
		'VCO_DIV' : 0b11111 << 18, # VCO_DIV[4:0] VCO Divider Value
		'OUTB_PWR' : 0b111111 << 12,
		'OUTA_PWR' : 0b111111 << 6,
		'OUTB_PD' : 1 << 5,
		'OUTA_PD' : 1 << 4,
		},
	#04
		{
		'PFD_DLY' : 0b111 << 29,
		'FL_FRCE' : 1 << 28,
		'FL_TOC' : 0b111111111111 << 16,
		'FL_CPG' : 0b11111 << 11,
		'CPG_BLEED' : 0b111111 << 4,
		},
	#05
		{
		'OUT_LDEN' : 1 << 24,
		'OSC_FREQ' : 0b111 << 21,
		'BUFEN_DIS' : 1 << 20,
		'VCO_SEL_MODE' : 0b11 << 15,
		'OUTB_MUX' : 0b11 << 13,
		'OUTA_MUX' : 0b11 << 11,
		'0_DLY' : 1 << 10,
		'MODE' : 0b11 << 8,
		'PWDN_MODE' : 0b111 << 5,
		'RESET' : 1 << 4,
		},
	#06
		{
		'RD_DIAGNOSATICS' : 0b11111111111111111111 << 11,
		'RDADDR' : 0b1111 << 5,
		'UWIRE_LOCK' : 1 << 4,
		},
	#07
		{
		'FL_SELECT' : 0b11111 << 26,
		'FL_PINMODE' : 0b111 << 23,
		'FL_INV' : 1 << 22,
		'MUXOUT_SELECT' : 0b11111 << 17,
		'MUX_INV' : 1 << 16,
		'MUXOUT_PINMODE' : 0b111 << 13,
		'LD_SELECT' : 0b11111 << 8,
		'LD_INV' : 1 << 7,
		'LD_PINMODE' : 0b111 << 4,
		},
	#08
		None,
	#09
		None,
	#10
		None,
	#11
		None,
	#12
		None,
	#13
		{
		'DLD_ERR_CNT' : 0b1111 << 28,
		'DLD_PASS_CNT' : 0b1111111111 << 18,
		'DLD_TOL' : 0b111 << 15,
		},
	#14
		None,
	#15
		{
		'VCO_CAP_MAN' : 1 << 12,
		'VCO_CAPCODE' : 0b11111111 << 4,
		},
	]

	MASK_DIAG = {
		'VCO_SELECT': 0b11 << 18+11,
		'FIN_DETECT': 0b1 << 17+11,
		'OSCIN_DETECT': 0b1 << 16+11,
		'VCO_DETECT': 0b1 << 15+11,
		'CAL_RUNNING': 0b1 << 10+11,
		'VCO_RAIL_HIGH': 0b1 << 9+11,
		'VCO_RAIL_LOW': 0b1 << 8+11,
		'VCO_TUNE_HIGH': 0b1 << 6+11,
		'VCO_TUNE_VALID': 0b1 << 5+11,
		'FLOUT_ON': 0b1 << 4+11,
		'DLD': 0b1 << 3+11,
		'LD_PINSTATE': 0b1 << 2+11,
		'CE_PINSTATE': 0b1 << 1+11,
		'BUFEN_PINSTATE': 0b1 << 0+11
	}

	CMD10 = 0b00100001000000000101000011001010 # Not disclosed to user
	CMD09 = 0b00000011110001111100000000111001 # Not disclosed to user
	CMD08 = 0b00100000011111011101101111111000 # Not disclosed to user
	
	FOSC = 10

	# Using recommanded parameter settings in the following datasheet
	# http://www.ti.com/lit/ds/symlink/lmx2581.pdf
	# Also borrow some lines from https://github.com/domagalski/snap-synth

	def __init__(self, interface, controller_name):
		super(LMX2581, self).__init__(interface, controller_name) 

#	def init(self):
#
#		# Here is the booting sequence of LMX2581 according to 8.5.2
#		# After reset, pretty much registers load their default/optimal values
#		# No further intervention is needed.
#
#		self.reset()
#
#		# Program some registers
#
#		# Register R15: ... to be complete
#
#		# Register R13: Page 30: 8.6.1.2
#		freq_pd = self.FOSC / 1
#		if freq_pd > 130:
#			DLD_TOL = 0
#		elif freq_pd > 80 and freq_pd < 130:
#			DLD_TOL = 1
#		elif freq_pd > 60 and freq_pd <= 80:
#			DLD_TOL = 2
#		elif freq_pd > 45 and freq_pd <= 60:
#			DLD_TOL = 3
#		elif freq_pd > 30 and freq_pd <= 45:
#			DLD_TOL = 4
#		else:
#			DLD_TOL = 5
#		r13 = self._set(0x4100,4,self.M13_DLD_ERR_CNT)
#		r13 = self._set(r13, 32, self.M13_DLD_PASS_CNT)
#		r13 = self._set(r13, DLD_TOL, self.M13_DLD_TOL)
#		self.write(r13, self.A13)
#
#		# Register R07: Page 31: 8.6.1.4
#		r07 = self._set(0, 0, self.M07_FL_SELECT)
#		r07 = self._set(r07, 2, self.M07_FL_PINMODE)
#		r07 = self._set(r07, 0, self.M07_FL_INV)
#		r07 = self._set(r07, 4, self.M07_MUXOUT_SELECT)
#		r07 = self._set(r07, 0, self.M07_MUX_INV)
#		r07 = self._set(r07, 1, self.M07_MUXOUT_PINMODE)
#		r07 = self._set(r07, 2, self.M07_LD_SELECT)
#		r07 = self._set(r07, 0, self.M07_LD_INV)
#		r07 = self._set(r07, 0, self.M07_LD_PINMODE)
#		self.write(r07, self.A07)
#
#		# Register R06: Page 33: 8.6.1.5
#		# Point RDADDR to R06, because its good for diagnostics
#		r06 = self._set(0x400, 6, self.M06_RDADDR)
#		self.write(r06, self.A06)
#
#		# Register R05: Page 34: 8.6.1.6
#		r05 = self._set(0, 0, self.M05_OUT_LDEN)
#		r05 = self._set(r05, 0, self.M05_OSC_FREQ)
#		r05 = self._set(r05, 0, self.M05_BUFEN_DIS)
#		r05 = self._set(r05, 0, self.M05_VCO_SEL_MODE)
#		r05 = self._set(r05, 0, self.M05_OUTB_MUX)
#		r05 = self._set(r05, 0, self.M05_OUTA_MUX)
#		r05 = self._set(r05, 0, self.M05_0_DLY)
#		r05 = self._set(r05, 0, self.M05_MODE)
#		r05 = self._set(r05, 0, self.M05_PWDN_MODE)
#		r05 = self._set(r05, 0, self.M05_RESET)
#		self.write(r05, self.A05)
#
#		# Register R04: Page 36: 8.6.1.7
#		r04 = self._set(0, 0, self.M04_PFD_DLY)
#		r04 = self._set(r04, 0, self.M04_PFD_DLY)
#		r04 = self._set(r04, 0, self.M04_FL_FRCE)
#		r04 = self._set(r04, 0, self.M04_FL_TOC)
#		r04 = self._set(r04, 0, self.M04_FL_CPG)
#		r04 = self._set(r04, 0, self.M04_CPG_BLEED)
#		self.write(r04, self.A04)
#
#		# Register R03: Page 38: 8.6.1.8
#		r03 = self._set(0x20000000, 0, self.M03_VCO_DIV)
#		r03 = self._set(r03, 15, self.M03_OUTB_PWR)
#		r03 = self._set(r03, 15, self.M03_OUTA_PWR)
#		r03 = self._set(r03, 0, self.M03_OUTB_PD)
#		r03 = self._set(r03, 0, self.M03_OUTA_PD)
#		self.write(r03, self.A03)
#
#		# Register R02: Page 39: 8.6.1.9
#		r02 = self._set(0x04000000, 0, self.M02_OSC_2X)
#		r02 = self._set(r02, 1, self.M02_CPP)
#		r02 = self._set(r02, 0, self.M02_PLL_DEN)
#		self.write(r02, self.A02)
#
#		# Register R01: Page 40: 8.6.1.10
#		r01 = self._set(0, 0, self.M01_CPG)
#		r01 = self._set(r01, 0, self.M01_VCO_SEL)
#		r01 = self._set(r01, 0, self.M01_PLL_NUM)
#		r01 = self._set(r01, 0, self.M01_FRAC_ORDER)
#		r01 = self._set(r01, 1, self.M01_PLL_R)
#		self.write(r01, self.A01)
#
#		# Register R00: Page 41: 8.6.1.11
#		r00 = self._set(0, 0, self.M00_ID)
#		r00 = self._set(r00, 0, self.M00_FRAC_DITHER)
#		r00 = self._set(r00, 0, self.M00_NO_FCAL)
#		r00 = self._set(r00, 7, self.M00_PLL_N)
#		r00 = self._set(r00, 0, self.M00_PLL_NUM)
#		self.write(r00, self.A00)
#
	def powerUp(self):
		self.setWord(0, "PWDN_MODE")

	def powerDown(self):
		self.setWord(1, "PWDN_MODE")

	def outputPower(self,p=15):
		self.setWord(p, "OUTA_PWR")
		self.setWord(p, "OUTB_PWR")
#
#	def get_osc_values(self, synth_mhz, ref_signal):
#		"""
#		This function gets oscillator values
#		"""
#		# Equation for the output frequency.
#		# f_out = f_osc * OSC_2X / PLL_R * (PLL_N + PLL_NUM/PLL_DEN) / VCO_DIV
#		# XXX Right now, I'm not going to use OSC_2X or PLL_R, so this becomes
#		# f_out = f_osc * (PLL_N + PLL_NUM/PLL_DEN) / VCO_DIV
#		
#		# Get a good VCO_DIV. The minimum VCO frequency is 1800.
#		vco_min = 1800; vco_max = 3800
#		if synth_mhz > vco_min and synth_mhz < vco_max:
#			# Bypass VCO_DIV by properly setting OUTA_MUX and OUTB_MUX
#			VCO_DIV = None
#		else:
#			vco_guess = int(vco_min / synth_mhz) + 1
#			VCO_DIV = vco_guess + vco_guess%2
#		
#		# Get PLLN, PLL_NUM, and PLL_DEN
#		pll = (1 if VCO_DIV is None else VCO_DIV) * synth_mhz / ref_signal
#		PLL_N = int(pll)
#		frac = pll - PLL_N
#		if frac < 1.0/(1<<22): # smallest fraction on the synth
#			PLL_NUM = 0
#			PLL_DEN = 1
#		else:
#			fraction = _frac.Fraction(frac).limit_denominator(1<<22)
#			PLL_NUM = fraction.numerator
#			PLL_DEN = fraction.denominator
#
#		return (PLL_N, PLL_NUM, PLL_DEN, VCO_DIV)
#
#	def setFreq(self, synth_mhz):
#
#		PLL_N, PLL_NUM, PLL_DEN, VCO_DIV = self.get_osc_values(synth_mhz,self.FOSC)
#
#		# Select the VCO frequency
#		# VCO1: 1800 to 2270 NHz
#		# VCO2: 2135 to 2720 MHz
#		# VCO3: 2610 to 3220 MHz
#		# VCO4: 3075 to 3800 MHz
#		freq_vco = freq_pd * (PLL_N + float(PLL_NUM)/PLL_DEN)
#		if freq_vco >= 1800 and freq_vco <= 2270:
#			VCO_SEL = 0
#		elif freq_vco >= 2135 and freq_vco <= 2720:
#			VCO_SEL = 1
#		elif freq_vco >= 2610 and freq_vco <= 3220:
#			VCO_SEL = 2
#		elif freq_vco >= 3075 and freq_vco <= 3800:
#			VCO_SEL = 3
#		else:
#			raise ValueError('VCO frequency is out of range.')
#		self.write(VCO_SEL, self.A01, self.M01_VCO_SEL)
#
#		# Dithering is set in R0, but it is needed for R1 stuff.
#		if PLL_NUM and PLL_DEN > 200 and not PLL_DEN % 2 and not PLL_DEN % 3:
#			FRAC_DITHER = 2
#		else:
#			FRAC_DITHER = 3
#		self.write(FRAC_DITHER, self.A00, self.M00_FRAC_DITHER)
#			
#		# Get the Fractional modulator order
#		if not PLL_NUM:
#			FRAC_ORDER = 0
#		elif PLL_DEN < 20:
#			FRAC_ORDER = 1
#		elif PLL_DEN % 3 and FRAC_DITHER == 3:
#			FRAC_ORDER = 3
#		else:
#			FRAC_ORDER = 2
#		self.write(FRAC_ORDER, self.A01, self.M01_FRAC_ORDER)
#
#		# Here is the booting sequence after changing frequency according to 8.5.3
#
#		# 1. (optional) If the OUTx_MUX State is changing, program Register R5
#		# 2. (optional) If the VCO_DIV state is changing, program Register R3.
#		# See VCO_DIV[4:0] - VCO Divider Value if programming a to a value of 4.
#		if VCD_DIV == None:
#			self.write(0, self.A05, self.M05_OUTA_MUX)
#			self.write(0, self.A05, self.M05_OUTB_MUX)
#		else:
#			self.write(1, self.A05, self.M05_OUTA_MUX)
#			self.write(1, self.A05, self.M05_OUTB_MUX)
#			VCO_DIV = VCO_DIV / 2 - 1
#			self.write(VCO_DIV, self.A03, self.M03_VCO_DIV)
#
#		# 3. (optional) If the MSB of the fractional numerator or charge pump gain
#		# is changing, program register R1
#
#		PLL_NUM_H = (PLL_NUM & 0b1111111111000000000000) >> 12
#		PLL_NUM_L =  PLL_NUM & 0b0000000000111111111111
#
#		self.write(PLL_DEN, self.A02, self.M02_PLL_DEN)
#		self.write(PLL_NUM_H, self.A01, self.M01_PLL_NUM)
#		self.write(PLL_NUM_L, self.A00, self.M00_PLL_NUM)
#		self.write(PLL_N, self.A00, self.M00_PLL_N)
#
#		# Sleep 20ms
#		time.sleep(0.02)
#
#		# 4. (Required) Program register R0
#		# Activate frequency calibration
#		self.write(0, self.A00, self.M00_NO_FCAL)
		

	def write(self, data, addr=None, mask=None):
		if mask != None and addr != None:
			r = self.read(addr)
			r = self._set(r, data, mask)
			self.write(r, addr)
		elif mask == None and addr != None:
			cmd = (data & 0xfffffff0) | (addr & 0xf)
			self._write(cmd)
		elif mask == None and addr == None:
			self._write(data)
		else:
			raise ValueError("Invalid parameters")

	def read(self, addr):
		rid = self.getRegId('RDADDR')
		# Tell LMX2581 which register to read
		r06 = self._set(0x400, addr, self.DICTS[rid]['RDADDR'])
		self.write(r06, rid)
		# Read the register by issuing a dummy write
		self.write(self.CMD10)
		return self._read()

	def _set(self, d1, d2, mask=None):
		# Update some bits of d1 with d2, while keep other bits unchanged
		if mask:
			d1 = d1 & ~mask
			d2 = d2 * (mask & -mask)
		return d1 | d2

	def _get(self, data, mask):
		data = data & mask
		return data / (mask & -mask)

	def reset(self):
		self.setWord(1,'RESET')

	def getDiagnoses(self,name=None):
		diag = self.read(6)
		if name:
			if name not in self.MASK_DIAG:
				raise ValueError("Invalid parameter")
			mask = self.MASK_DIAG.get(name)
			return self._get(diag, mask)
		else:
			result = {}
			for name,mask in self.MASK_DIAG.items():
				result[name] = self._get(diag, mask)
			return result

	def getRegister(self,rid=None):
		if rid==None:
			regIdLst = [15,13,7,6,5,4,3,2,1,0]
			return [self.getRegister(regId) for regId in regIdLst]
		else:
			rval = self.read(rid)
			return {name: self._get(rval,mask) for name, mask in self.DICTS[rid].items()}

	def getWord(self,name):
		rid = self.getRegId(name)
		rval = self.read(rid)
		return self._get(rval,self.DICTS[rid][name])

	def setWord(self,value,name):
		rid = self.getRegId(name)
		self.write(value,rid,self.DICTS[rid][name])

	def getRegId(self,name):
		rid = None
		for d in self.DICTS:
			if d == None:
				continue
			if name in d:
				rid = self.DICTS.index(d)
				break
		if rid == None:
			raise ValueError("Invalid parameter")
		return rid

	def loadCfgFromFile(self,filename):
		f = open(filename)
		lines = [l.split("\t") for l in f.read().splitlines()]
		regs = [int(l[1].rstrip(),0) for l in lines]
		for reg in regs:
			self.write(reg)
				
