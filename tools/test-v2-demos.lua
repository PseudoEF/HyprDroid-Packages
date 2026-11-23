-- Run with Lua 5.4 from the Packages root. These mocks test module contracts, not Android isolation.
local function fixture(module, values)
    local snapshot, stateValues, events, timers
    stateValues, events, timers = {}, {}, {}
    local env = {
        state = {
            get = function(key, default)
                if stateValues[key] == nil then return default end
                return stateValues[key]
            end,
            set = function(key, value) stateValues[key] = value end,
        },
        system = {get = function(key) return values[key] end},
        timer = {every = function(id, interval) timers[id] = interval end},
        hypr = {ui = {
            render = function(tree) snapshot = tree end,
            on = function(kind, id, fn) events[kind .. ":" .. id] = fn end,
        }},
    }
    assert(loadfile("modules/" .. module .. "/main.lua", "t", env))()
    return function() return snapshot end, events, timers
end

local time = {["device.time"] = {date = "2026-11-23", time24 = "15:24:00", time12 = "3:24:00 PM"}}
local clock, clockEvents, timers = fixture("clock-tile", time)
assert(clock().children[2].value == "2026-11-23")
assert(clock().children[3].value == "15:24:00")
assert(timers.clock == 1000)
clockEvents["onChange:format24"]({value = false})
assert(clock().children[3].value == "3:24:00 PM")
time["device.time"].time12 = "3:24:01 PM"
clockEvents["onTimer:clock"]()
assert(clock().children[3].value == "3:24:01 PM")

local stats = {["battery.level"] = 64, ["battery.charging"] = false}
local battery, batteryEvents = fixture("battery-tile", stats)
assert(battery().children[2].value == "64%")
assert(battery().children[3].value == "Not charging")
assert(battery().children[4].value == 0.64)
stats["battery.level"], stats["battery.charging"] = nil, true
batteryEvents["onClick:refresh"]()
assert(battery().children[2].value == "Level unavailable")
assert(battery().children[3].value == "Charging")
assert(battery().children[4].id == "refresh")
print("Clock Tile and Battery Tile contracts verified")
