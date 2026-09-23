import { describe, expect, it } from 'vitest'
import type { WaferDataset } from '../../types/wafer'
import { waferCsv } from './export'

describe('waferCsv', () => {
  it('exports canonical die fields and escapes text', () => {
    const dataset: WaferDataset = {
      metadata: {
        product_id: 'DEMO',
        lot_id: 'LOT1',
        wafer_id: '01',
        flow_id: 'CP1',
        subcon: null,
        tester: null,
        test_program: null,
        probe_card: null,
        start_time: null,
        stop_time: null,
        notch: 'DOWN',
        rows: 1,
        columns: 1,
      },
      dies: [
        {
          row: 0,
          column: 0,
          source_char: 'I',
          soft_bin: 18,
          hard_bin: null,
          result: 'FAIL',
          description: 'Pout, "min"',
          test_values: null,
        },
      ],
      bins: [
        {
          bin: 18,
          char: 'I',
          description: 'Pout, "min"',
          count: 1,
          percentage: 1,
        },
      ],
      summary: {
        tested_die: 1,
        pass_die: 0,
        fail_die: 1,
        yield: 0,
      },
    }

    const csv = waferCsv(dataset)

    expect(csv).toContain('"0","0","I","18","","FAIL","Pout, ""min"""')
  })
})
