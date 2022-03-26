import os
import csv
import fire
import sys
import random

import constants
from common import prepare_opcodes, get_selection


dir_path = os.path.dirname(os.path.realpath(__file__))


class Program(object):
  """
  POD object for a program
  """

  def __init__(self, bytecode, measured_op_position):
    self.bytecode = bytecode
    self.measured_op_position = measured_op_position


class ProgramGenerator(object):
  """
  Sample program generator for EVM instrumentation

  If used with `--fullCsv`, will print out a CSV in the following format:
  ```
  | program_id | opcode_measured | measured_op_position | bytecode |
  ```

  A sample usage `python3 program_generator/pg_validation.py generate --count=2 --opsLimit=100 --seed=123123123`

  NOTE: `measured_op_position` doesn't take into account the specific instructions fired before the
  generated part starts executing. It is relative to the first instruction of the _generated_ part
  of the program. E.g.: `evmone` prepends `JUMPDESTI`, `openethereum_ewasm` prepends many instructions
  """

  def __init__(self, seed=0):
    random.seed(a=seed, version=2)

    opcodes = prepare_opcodes(os.path.join(dir_path, 'data', 'opcodes.csv'))
    selection = get_selection(os.path.join(dir_path, 'data', 'selection.csv'))

    self._operations = {int(op, 16): opcodes[op] for op in selection}

  def generate(self, fullCsv=False, count=1, opsLimit=None, bytecodeLimit=None, dominant=None, push=32, cleanStack=False, randomizePush=False, randomizeOpsLimit=False):
    """
    Main entrypoint of the CLI tool. Should dispatch to the desired generation routine and print
    programs to STDOUT. If no limits given then by default opsLimit=100

    Parameters:
    fullCsv (boolean): if set, will generate programs with accompanying data in CSV format
    count (int): the number of programs 
    opsLimit (int): the limit operations for a single program, including pushes as one
    randomizeOpsLimit (boolean): whether the limit of operations should be randomized, up to the value of opsLimit
    bytecodeLimit (int): the bytecode limit of a single program
    dominant: an opcode that is picked more often then others, probability ~0.5
    push: the range of default push used in the program, values 1..32, assign ops push1..push32
    randomizePush: whether size of arguments should be randomized, up to the value of push
    cleanStack: whether to clean stack after every opcode or not, default is not
    """
    
    if not opsLimit and not bytecodeLimit:
      opsLimit = 100

    opsLimitMax = opsLimit

    programs = []
    for i in range(count):
      if randomizeOpsLimit:
        opsLimit = random.randint(1, opsLimitMax)
      else:
        opsLimit = opsLimitMax

      program = self._generate_random_arithmetic(opsLimit, bytecodeLimit, dominant, push, cleanStack, randomizePush)
      programs.append(program)

    if fullCsv:
      writer = csv.writer(sys.stdout, delimiter=',', quotechar='"')

      program_ids = [i for i, program in enumerate(programs)]
      bytecodes = [program.bytecode for program in programs]

      header = ['program_id', 'bytecode']
      writer.writerow(header)

      rows = zip(program_ids, bytecodes)
      for row in rows:
        writer.writerow(row)
    else:
      for program in programs:
        print(program.bytecode)

  def _generate_random_arithmetic(self, opsLimit, bytecodeLimit, dominant, pushMax, cleanStack, randomizePush):
    """
    Generates one large programs with multiple arithmetic operations
    """

    if pushMax < 1 or pushMax > 32:
      raise ValueError(pushMax)

    # generated bytecode
    bytecode = ''
    # number of operations including pushes
    ops_count = 0
    if not cleanStack:
      previous_nreturns = 0
    # constant list of arithmetic operations
    arithmetic_ops = [0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08, 0x09]  # ADD MUL SUB DIV SDIV MOD SMOD ADDMOD MULMOD
    exp_ops = [0x0a]  # EXP
    bitwise_ops = [0x16, 0x17, 0x18, 0x19]  # AND OR XOR NOT
    byte_ops = [0x1a, 0x0b]  # BYTE SIGNEXTEND
    shift_ops = [0x1b, 0x1c, 0x1d]  # SHL, SHR, SAR
    comparison_ops = [0x10, 0x11, 0x12, 0x13, 0x14]  # LT, GT, SLT, SGT, EQ
    iszero_ops = [0x15]  # ISZERO
    # ADDRESS, ORIGIN, CALLER, CALLVALUE, CODESIZE, GASPRICE, COINBASE, TIMESTAMP, NUMBER
    # DIFFICULTY, GASLIMIT, CHAINID, SELFBALANCE, PC, MSIZE, GAS
    simple_nullary_ops = [0x30, 0x32, 0x33, 0x34, 0x38, 0x3a, 0x41, 0x42, 0x43,
                          0x44, 0x45, 0x46, 0x47, 0x58, 0x59, 0x5a]
    pop_ops = [0x50]
    jumpdest_ops = [0x5b]  # JUMPDEST
    dup_ops = [0x80, 0x81, 0x82, 0x83, 0x84, 0x85, 0x86, 0x87, 0x88, 0x89, 0x8a, 0x8b, 0x8c, 0x8d, 0x8e, 0x8f]
    swap_ops = [0x90, 0x91, 0x92, 0x93, 0x94, 0x95, 0x96, 0x97, 0x98, 0x99, 0x9a, 0x9b, 0x9c, 0x9d, 0x9e, 0x9f]

    all_ops = []
    all_ops.extend(arithmetic_ops)
    all_ops.extend(exp_ops)
    all_ops.extend(bitwise_ops)
    all_ops.extend(byte_ops)
    all_ops.extend(shift_ops)
    all_ops.extend(comparison_ops)
    all_ops.extend(iszero_ops)
    all_ops.extend(simple_nullary_ops)
    all_ops.extend(pop_ops)
    all_ops.extend(jumpdest_ops)
    # PUSHes DUPs and SWAPs overwhelm the others if treated equally. We pick the class with probability as any
    # other OPCODE, and then the variant is drawn in a subsequent `random.choice` with equal probability.
    all_ops.append("DUPclass")
    all_ops.append("SWAPclass")

    if dominant and dominant not in all_ops:
      raise ValueError(dominant)

    while (not opsLimit or ops_count < opsLimit) and (not bytecodeLimit or len(bytecode)<2*bytecodeLimit):
      if dominant:
        if random.random() < 0.5:
          op = dominant
        else:
          op = random.choice(all_ops)
      else:
        op = random.choice(all_ops)

      if op == "DUPclass":
        op = random.choice(dup_ops)
      elif op == "SWAPclass":
        op = random.choice(swap_ops)

      operation = self._operations[op]
      arity = int(operation['Removed from stack'])
      nreturns = int(operation['Added to stack'])

      # determine how many args we need to push on the stack and push
      # some value have remained on the stack, unless we're in `cleanStack` mode, whereby they had been popped
      needed_pushes = arity if cleanStack else (arity - previous_nreturns)
      # i.e. 23 from 0x23
      opcode = operation['Value'][2:4]
      if op in byte_ops:  # BYTE SIGNEXTEND needs 0-31 value on the top of the stack
        bytecode += self._random_push(pushMax, randomizePush) if cleanStack or previous_nreturns == 0 else ""
        bytecode += self._random_push_less_32()
      elif op in shift_ops:  # SHL, SHR, SAR need 0-255 value on the top of the stack
        bytecode += self._random_push(pushMax, randomizePush) if cleanStack or previous_nreturns == 0 else ""
        bytecode += self._random_push(1, False)
      else:
        bytecode += ''.join([self._random_push(pushMax, randomizePush) for _ in range(needed_pushes)])
      ops_count += needed_pushes

      # push the current random opcode
      bytecode += opcode
      ops_count += 1

      # Pop any results to keep the stack clean for the next iteration. Otherwise mark how many returns remain on
      # the stack after the OPCODE executed.
      if cleanStack:
        # empty the stack
        bytecode += '50' * nreturns  # POP
        ops_count += nreturns
      else:
        previous_nreturns = nreturns

    return Program(bytecode, ops_count)

  def _random_push(self, pushMax, randomizePush):
    if randomizePush:
      push = random.randint(1, pushMax)
    else:
      push = pushMax

    value = random.getrandbits(8*push)
    value = hex(value)
    value = value[2:]
    if len(value) < 2*push:
      value = (2*push-len(value))*'0' + value
    op_num = 6 * 16 + push - 1  # 0x60 is PUSH1
    op = hex(op_num)[2:]
    return op + value

  def _random_push_less_32(self):
    value = random.randint(0, 31)
    value = hex(value)
    value = value[2:]
    if len(value) < 2:
      value = (2-len(value))*'0' + value
    return '60' + value

  def _fill_opcodes_push_dup_swap(self, opcodes):
    pushes = constants.EVM_PUSHES
    dups = constants.EVM_DUPS
    swaps = constants.EVM_SWAPS

    pushes = self._opcodes_dict_push_dup_swap(pushes, [0] * len(pushes), [1] * len(pushes), parameter='00')
    opcodes = {**opcodes, **pushes}
    dups = self._opcodes_dict_push_dup_swap(dups, range(1, len(dups)), range(2, len(dups)+1))
    opcodes = {**opcodes, **dups}
    swaps = self._opcodes_dict_push_dup_swap(swaps, range(2, len(swaps)+1), range(2, len(swaps)+1))
    opcodes = {**opcodes, **swaps}
    return opcodes

  def _opcodes_dict_push_dup_swap(self, source, removeds, addeds, parameter=None):
    source_list = source.split()
    opcodes = source_list[::2]
    names = source_list[1::2]
    new_part = {
      opcode: {
        'Value': opcode,
        'Mnemonic': name,
        'Removed from stack': removed,
        'Added to stack': added,
        'Parameter': parameter
      } for opcode, name, removed, added in zip(opcodes, names, removeds, addeds)
    }

    return new_part

def main():
  fire.Fire(ProgramGenerator, name='generate')

if __name__ == '__main__':
  main()
